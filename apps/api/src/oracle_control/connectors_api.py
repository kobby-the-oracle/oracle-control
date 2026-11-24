from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from oracle_control.connectors.cloudtrail import CloudTrailConnector
from oracle_control.connectors.otel import OpenTelemetrySpanAdapter
from oracle_control.db import get_db
from oracle_control.entities import AuditRecord, EventRecord
from oracle_control.evidence import event_digests
from oracle_control.security import require_roles

router=APIRouter(prefix="/v1/connectors",tags=["source connectors"])

class CloudTrailBatch(BaseModel):
    records:list[dict[str,Any]]=Field(min_length=1,max_length=500)

class OTelBatch(BaseModel):
    spans:list[dict[str,Any]]=Field(min_length=1,max_length=500)

def persist_normalized_event(db:Session,event,principal):
    tenant=principal["tenant_id"]
    payload_digest,event_digest=event_digests(event.model_dump(mode="json"))
    existing=db.query(EventRecord).filter_by(tenant_id=tenant,event_id=event.event_id).first()
    if existing:
        if existing.event_sha256!=event_digest:
            raise HTTPException(409,f"Conflicting source replay: {event.event_id}")
        return {"event_id":event.event_id,"status":"duplicate"}
    row=EventRecord(tenant_id=tenant,event_id=event.event_id,source_system=event.source.system,
        source_event_id=event.source.event_id,event_type=event.event_type,occurred_at=event.occurred_at,
        agent_id=event.agent_id,run_id=event.run_id,session_id=event.session_id,\n        parent_agent_id=event.parent_agent_id,parent_run_id=event.parent_run_id,\n        credential_ref=event.credential_ref,actor_id=event.actor_id,resource_id=event.resource_id,
        confidence=event.relationship_confidence,payload=event.payload,payload_sha256=payload_digest,
        event_sha256=event_digest,redaction_applied=event.redaction_applied)
    db.add(row)
    db.flush()
    db.add(AuditRecord(tenant_id=tenant,actor=principal["subject"],action="connector.event_ingested",
        object_type="event",object_id=event.event_id,details={"source":event.source.system,"sha256":event_digest}))
    return {"event_id":event.event_id,"status":"ingested"}

@router.post("/aws/cloudtrail/events")
def ingest_cloudtrail(body:CloudTrailBatch,principal=Depends(require_roles("collector","admin")),db:Session=Depends(get_db)):
    connector=CloudTrailConnector();results=[]
    try:
        for record in body.records:
            event=connector.parse(record,tenant_id=principal["tenant_id"])
            results.append(persist_normalized_event(db,event,principal))
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    except Exception:
        db.rollback()
        raise
    return {"connector":connector.name,"received":len(body.records),"results":results}

@router.post("/opentelemetry/spans")
def ingest_otel(body:OTelBatch,principal=Depends(require_roles("collector","admin")),db:Session=Depends(get_db)):
    adapter=OpenTelemetrySpanAdapter();results=[]
    try:
        for span in body.spans:
            event=adapter.parse(span,tenant_id=principal["tenant_id"])
            results.append(persist_normalized_event(db,event,principal))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"connector":adapter.name,"received":len(body.spans),"results":results}

@router.get("/catalog")
def connector_catalog(principal=Depends(require_roles("analyst","auditor","admin"))):
    return {
        "available_record_adapters":[
            {"id":"aws-cloudtrail","status":"record-ingest-enabled","endpoint":"/v1/connectors/aws/cloudtrail/events"},
            {"id":"opentelemetry","status":"span-ingest-enabled","endpoint":"/v1/connectors/opentelemetry/spans"},
        ],
        "planned_source_families":["Azure Activity Logs","Google Cloud Audit Logs","Entra ID","Okta",
            "GitHub","Jira","Slack","ServiceNow","PostgreSQL","Snowflake","BigQuery",
            "Microsoft Defender","CrowdStrike","Splunk","Elastic"],
        "limitation":"These endpoints accept pushed records/spans. They do not yet poll source APIs, manage credentials, maintain cursors or perform historical backfill."
    }
