from datetime import datetime, timezone
from typing import Any
from fastapi import Depends, FastAPI, HTTPException, Query, Response
from sqlalchemy.orm import Session
from oracle_control.cases import router as cases_router
from oracle_control.config import EVIDENCE_DIR
from oracle_control.db import Base, engine, get_db
from oracle_control.entities import AuditRecord, EventRecord
from oracle_control.evidence import event_digests
from oracle_control.evidence_api import router as evidence_router
from oracle_control.models import AgentEventIn\nfrom oracle_control.agents import router as agents_router\nfrom oracle_control.authority import router as authority_router\nfrom oracle_control.intelligence import router as intelligence_router
from oracle_control.security import tenant_principal

app = FastAPI(
    title="ORACLE CONTROL API",
    version="0.2.0",
    description="Evidence-centred AI incident investigation. Enterprise foundation; deployment hardening remains in progress.",
)
app.include_router(cases_router)
app.include_router(evidence_router)\napp.include_router(agents_router)\napp.include_router(authority_router)\napp.include_router(intelligence_router)

@app.on_event("startup")
def initialise_storage():
    EVIDENCE_DIR.mkdir(parents=True,exist_ok=True)
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health() -> dict[str,str]:
    return {"status":"ok","service":"oracle-control-api"}

@app.post("/v1/events",status_code=201)
def ingest_event(event:AgentEventIn, response:Response, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    if event.tenant_id != principal["tenant_id"]:
        raise HTTPException(403,"Event tenant does not match authenticated tenant")
    event_dict=event.model_dump(mode="json")
    payload_digest,event_digest=event_digests(event_dict)
    existing=db.query(EventRecord).filter_by(tenant_id=event.tenant_id,event_id=event.event_id).first()
    if existing:
        if existing.event_sha256 != event_digest:
            raise HTTPException(409,"event_id already exists for this tenant with different content")
        response.status_code=200\n        return {"event":event_dict,"ingested_at":existing.ingested_at,"payload_sha256":existing.payload_sha256,
            "canonical_event_sha256":existing.event_sha256,"duplicate":True}
    row=EventRecord(tenant_id=event.tenant_id,event_id=event.event_id,
        source_system=event.source.system,source_event_id=event.source.event_id,event_type=event.event_type,
        occurred_at=event.occurred_at,agent_id=event.agent_id,run_id=event.run_id,actor_id=event.actor_id,
        resource_id=event.resource_id,confidence=event.relationship_confidence,payload=event.payload,
        payload_sha256=payload_digest,event_sha256=event_digest,redaction_applied=event.redaction_applied)
    db.add(row)
    db.add(AuditRecord(tenant_id=event.tenant_id,actor=principal["subject"],action="event.ingested",
        object_type="event",object_id=event.event_id,details={"source":event.source.system,"sha256":event_digest}))
    db.commit()
    db.refresh(row)
    return {"event":event_dict,"ingested_at":row.ingested_at,"payload_sha256":payload_digest,
        "canonical_event_sha256":event_digest,"duplicate":False}

@app.get("/v1/events")
def list_events(agent_id:str|None=None,run_id:str|None=None,
    limit:int=Query(default=100,ge=1,le=1000),principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    q=db.query(EventRecord).filter_by(tenant_id=principal["tenant_id"])
    if agent_id:q=q.filter_by(agent_id=agent_id)
    if run_id:q=q.filter_by(run_id=run_id)
    rows=q.order_by(EventRecord.occurred_at.asc()).limit(limit).all()
    return [{"event_id":r.event_id,"source":{"system":r.source_system,"event_id":r.source_event_id},
        "event_type":r.event_type,"occurred_at":r.occurred_at,"ingested_at":r.ingested_at,
        "agent_id":r.agent_id,"run_id":r.run_id,"actor_id":r.actor_id,"resource_id":r.resource_id,
        "relationship_confidence":r.confidence,"payload":r.payload,"payload_sha256":r.payload_sha256,
        "canonical_event_sha256":r.event_sha256,"redaction_applied":r.redaction_applied} for r in rows]

@app.get("/v1/audit")
def list_audit(limit:int=Query(default=100,ge=1,le=1000),principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    rows=db.query(AuditRecord).filter_by(tenant_id=principal["tenant_id"]).order_by(AuditRecord.occurred_at.desc()).limit(limit).all()
    return [{"id":r.id,"actor":r.actor,"action":r.action,"object_type":r.object_type,
        "object_id":r.object_id,"details":r.details,"occurred_at":r.occurred_at} for r in rows]

@app.get("/v1/meta")
def metadata() -> dict[str,Any]:
    return {"service":"ORACLE CONTROL","api_version":app.version,"server_time":datetime.now(timezone.utc).isoformat(),
        "storage":"configured SQL database + local evidence filesystem","production_ready":False,
        "note":"Configure managed object storage, OIDC, migrations, key management and hardened deployment before production."}
