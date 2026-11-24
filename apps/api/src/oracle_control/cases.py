import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from oracle_control.db import get_db
from oracle_control.custody import append_custody
from oracle_control.entities import AuditRecord, CaseRecord, CustodyRecord, EvidenceRecord, EventRecord, FindingRecord
from oracle_control.evidence import sha256_hex
from oracle_control.storage import EvidenceStorageError, read_evidence
from oracle_control.security import require_roles

router = APIRouter(prefix="/v1/cases", tags=["investigations"])


class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str = ""
    agent_ids: list[str] = Field(default_factory=list)
    severity: str = "medium"


class FindingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    statement: str = Field(min_length=3)
    confidence: str = "unknown"
    evidence_ids: list[str] = Field(default_factory=list)


@router.post("", status_code=201)
def create_case(body: CaseCreate, principal=Depends(require_roles('analyst', 'admin')), db: Session = Depends(get_db)):
    if body.severity not in {"critical", "high", "medium", "low"}:
        raise HTTPException(422, "Invalid severity")
    row = CaseRecord(
        id=str(uuid4()), tenant_id=principal["tenant_id"], title=body.title,
        description=body.description, agent_ids=body.agent_ids, severity=body.severity,
        created_by=principal["subject"],
    )
    db.add(row)
    db.add(AuditRecord(
        tenant_id=row.tenant_id, actor=principal["subject"], action="case.created",
        object_type="case", object_id=row.id, details={"severity": row.severity, "agent_ids": row.agent_ids},
    ))
    db.commit()
    return {
        "id": row.id, "title": row.title, "description": row.description,
        "agent_ids": row.agent_ids, "severity": row.severity, "status": row.status,
        "created_at": row.created_at,
    }


@router.get("")
def list_cases(principal=Depends(require_roles('analyst', 'auditor', 'admin')), db: Session = Depends(get_db)):
    rows = db.query(CaseRecord).filter_by(tenant_id=principal["tenant_id"]).order_by(
        CaseRecord.created_at.desc()
    ).all()
    return [
        {"id": r.id, "title": r.title, "agent_ids": r.agent_ids, "severity": r.severity,
         "status": r.status, "created_at": r.created_at}
        for r in rows
    ]


@router.get("/{case_id}")
def get_case(case_id: str, principal=Depends(require_roles('analyst', 'auditor', 'admin')), db: Session = Depends(get_db)):
    row = db.query(CaseRecord).filter_by(
        id=case_id, tenant_id=principal["tenant_id"]
    ).first()
    if not row:
        raise HTTPException(404, "Case not found")
    return {
        "id": row.id, "title": row.title, "description": row.description,
        "agent_ids": row.agent_ids, "severity": row.severity, "status": row.status,
        "created_at": row.created_at,
        "findings": [
            {"id": f.id, "title": f.title, "statement": f.statement,
             "confidence": f.confidence, "evidence_ids": f.evidence_ids}
            for f in row.findings
        ],
    }


@router.post("/{case_id}/findings", status_code=201)
def add_finding(
    case_id: str, body: FindingCreate, principal=Depends(require_roles('analyst', 'admin')), db: Session = Depends(get_db)
):
    tenant = principal["tenant_id"]
    case = db.query(CaseRecord).filter_by(id=case_id, tenant_id=tenant).first()
    if not case:
        raise HTTPException(404, "Case not found")
    if body.confidence not in {"directly_observed", "correlated", "inferred", "unknown"}:
        raise HTTPException(422, "Invalid confidence")
    if body.evidence_ids:
        found = {
            e.id for e in db.query(EvidenceRecord).filter(
                EvidenceRecord.tenant_id == tenant,
                EvidenceRecord.id.in_(body.evidence_ids),
            ).all()
        }
        if found != set(body.evidence_ids):
            raise HTTPException(422, "Evidence reference missing or belongs to another tenant")
    row = FindingRecord(
        id=str(uuid4()), case_id=case_id, tenant_id=tenant, title=body.title,
        statement=body.statement, confidence=body.confidence, evidence_ids=body.evidence_ids,
    )
    db.add(row)
    db.add(AuditRecord(
        tenant_id=tenant, actor=principal["subject"], action="finding.created",
        object_type="finding", object_id=row.id, details={"case_id": case_id},
    ))
    db.commit()
    return {
        "id": row.id, "case_id": case_id, "title": row.title,
        "confidence": row.confidence, "evidence_ids": row.evidence_ids,
    }


@router.patch("/{case_id}/status")
def update_case_status(
    case_id: str, status: str, principal=Depends(require_roles('analyst', 'admin')), db: Session = Depends(get_db)
):
    if status not in {"open", "investigating", "contained", "resolved", "closed"}:
        raise HTTPException(422, "Invalid case status")
    row = db.query(CaseRecord).filter_by(
        id=case_id, tenant_id=principal["tenant_id"]
    ).first()
    if not row:
        raise HTTPException(404, "Case not found")
    previous = row.status
    row.status = status
    db.add(AuditRecord(
        tenant_id=row.tenant_id, actor=principal["subject"], action="case.status_changed",
        object_type="case", object_id=row.id, details={"from": previous, "to": status},
    ))
    db.commit()
    return {"id": row.id, "status": row.status}


@router.get("/{case_id}/export")
def export_case(case_id: str, principal=Depends(require_roles('analyst', 'auditor', 'admin')), db: Session = Depends(get_db)):
    tenant = principal["tenant_id"]
    case = db.query(CaseRecord).filter_by(id=case_id, tenant_id=tenant).first()
    if not case:
        raise HTTPException(404, "Case not found")
    evidence = db.query(EvidenceRecord).filter_by(tenant_id=tenant, case_id=case_id).all()
    findings = db.query(FindingRecord).filter_by(tenant_id=tenant, case_id=case_id).all()
    events = db.query(EventRecord).filter(EventRecord.tenant_id == tenant, EventRecord.agent_id.in_(case.agent_ids or ["__none__"])).order_by(EventRecord.occurred_at.asc()).limit(10000).all()
    manifest = {
        "format": "oracle-control-case-export-v1",
        "case_id": case.id,
        "tenant_id": tenant,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "integrity_note": "SHA-256 verifies included bytes against collection digests; it does not prove source authenticity or collection completeness.",
        "evidence": [],
        "custody": [],
        "event_count": len(events),
        "collection_limitations": ["Export includes only event records currently ingested for agents explicitly linked to this case.", "Absence of an event in this package does not prove the action did not occur."] ,
    }
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("case.json", json.dumps({
            "id": case.id, "title": case.title, "description": case.description,
            "agent_ids": case.agent_ids, "severity": case.severity, "status": case.status,
            "created_at": case.created_at.isoformat(),
        }, default=str, indent=2))
        archive.writestr("events.json", json.dumps([{
            "event_id": e.event_id, "source_system": e.source_system, "source_event_id": e.source_event_id,
            "event_type": e.event_type, "occurred_at": e.occurred_at.isoformat(),
            "ingested_at": e.ingested_at.isoformat(), "agent_id": e.agent_id, "run_id": e.run_id,
            "session_id": e.session_id, "parent_agent_id": e.parent_agent_id, "parent_run_id": e.parent_run_id,
            "credential_ref": e.credential_ref, "actor_id": e.actor_id, "resource_id": e.resource_id,
            "confidence": e.confidence, "payload": e.payload, "payload_sha256": e.payload_sha256,
            "event_sha256": e.event_sha256, "redaction_applied": e.redaction_applied,
        } for e in events], default=str, indent=2))
        archive.writestr("findings.json", json.dumps([
            {"id": f.id, "title": f.title, "statement": f.statement,
             "confidence": f.confidence, "evidence_ids": f.evidence_ids}
            for f in findings
        ], indent=2))
        for item in evidence:
            try:
                raw = read_evidence(item.storage_path)
            except FileNotFoundError as exc:
                raise HTTPException(410, f"Evidence bytes unavailable: {item.id}") from exc
            except EvidenceStorageError as exc:
                raise HTTPException(502, str(exc)) from exc
            actual = sha256_hex(raw)
            if len(raw) != item.byte_length or actual != item.sha256:
                raise HTTPException(409, f"Evidence integrity check failed: {item.id}")
            archive_path = f"evidence/{item.id}/{Path(item.filename).name}"
            archive.writestr(archive_path, raw)
            append_custody(db, tenant_id=tenant, evidence_id=item.id, actor=principal["subject"], action="evidence.exported", details={"case_id":case_id,"sha256":item.sha256})
            db.flush()
            custody_rows = db.query(CustodyRecord).filter_by(
                tenant_id=tenant, evidence_id=item.id
            ).order_by(CustodyRecord.id.asc()).all()
            manifest["custody"].append([
                {"sequence": r.id, "actor": r.actor, "action": r.action,
                 "details": r.details, "previous_hash": r.previous_hash,
                 "record_hash": r.record_hash, "occurred_at": r.occurred_at.isoformat()}
                for r in custody_rows
            ])
            manifest["evidence"].append({
                "id": item.id, "filename": item.filename, "path": archive_path,
                "sha256": item.sha256, "byte_length": item.byte_length,
                "source_system": item.source_system, "source_reference": item.source_reference,
                "collected_by": item.collected_by, "collected_at": item.collected_at.isoformat(),
            })
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
    db.add(AuditRecord(
        tenant_id=tenant, actor=principal["subject"], action="case.exported",
        object_type="case", object_id=case_id,
        details={"evidence_count": len(evidence), "finding_count": len(findings)},
    ))
    db.commit()
    stream.seek(0)
    return StreamingResponse(
        stream, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="oracle-control-{case_id}.zip"'},
    )
