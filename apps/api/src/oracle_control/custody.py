from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from oracle_control.db import get_db
from oracle_control.entities import AuditRecord, CustodyRecord, EvidenceRecord
from oracle_control.evidence import canonical_json, sha256_hex
from oracle_control.security import require_roles

router = APIRouter(prefix="/v1/custody", tags=["chain of custody"])
GENESIS = "0" * 64


def utc_normalized(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def append_custody(
    db: Session, *, tenant_id: str, evidence_id: str, actor: str, action: str, details: dict | None = None
):
    previous = db.query(CustodyRecord).filter_by(
        tenant_id=tenant_id, evidence_id=evidence_id
    ).order_by(CustodyRecord.id.desc()).first()
    previous_hash = previous.record_hash if previous else GENESIS
    occurred_at = datetime.now(timezone.utc)
    record_details = details or {}
    body = {
        "tenant_id": tenant_id, "evidence_id": evidence_id, "actor": actor,
        "action": action, "details": record_details, "previous_hash": previous_hash,
        "occurred_at": occurred_at.isoformat(),
    }
    row = CustodyRecord(
        tenant_id=tenant_id, evidence_id=evidence_id, actor=actor, action=action,
        details=record_details, previous_hash=previous_hash,
        record_hash=sha256_hex(canonical_json(body)), occurred_at=occurred_at,
    )
    db.add(row)
    return row


class TransferInput(BaseModel):
    to_actor: str = Field(min_length=1, max_length=256)
    note: str = ""


@router.get("/evidence/{evidence_id}")
def get_custody(evidence_id: str, principal=Depends(require_roles("analyst", "auditor", "admin")), db: Session = Depends(get_db)):
    tenant = principal["tenant_id"]
    evidence = db.query(EvidenceRecord).filter_by(id=evidence_id, tenant_id=tenant).first()
    if not evidence:
        raise HTTPException(404, "Evidence not found")
    rows = db.query(CustodyRecord).filter_by(
        tenant_id=tenant, evidence_id=evidence_id
    ).order_by(CustodyRecord.id.asc()).all()
    return [{
        "sequence": row.id, "actor": row.actor, "action": row.action,
        "details": row.details, "previous_hash": row.previous_hash,
        "record_hash": row.record_hash, "occurred_at": row.occurred_at,
    } for row in rows]


@router.post("/evidence/{evidence_id}/transfer", status_code=201)
def transfer_custody(
    evidence_id: str, body: TransferInput,
    principal=Depends(require_roles("analyst", "admin")), db: Session = Depends(get_db)
):
    tenant = principal["tenant_id"]
    evidence = db.query(EvidenceRecord).filter_by(id=evidence_id, tenant_id=tenant).first()
    if not evidence:
        raise HTTPException(404, "Evidence not found")
    row = append_custody(db, tenant_id=tenant, evidence_id=evidence_id,
        actor=principal["subject"], action="custody.transferred",
        details={"to_actor": body.to_actor, "note": body.note})
    db.add(AuditRecord(tenant_id=tenant, actor=principal["subject"], action="custody.transferred",
        object_type="evidence", object_id=evidence_id, details={"to_actor": body.to_actor}))
    db.commit()
    return {"sequence": row.id, "record_hash": row.record_hash, "previous_hash": row.previous_hash}


@router.get("/evidence/{evidence_id}/verify")
def verify_custody(
    evidence_id: str, principal=Depends(require_roles("analyst", "auditor", "admin")), db: Session = Depends(get_db)
):
    tenant = principal["tenant_id"]
    evidence = db.query(EvidenceRecord).filter_by(id=evidence_id, tenant_id=tenant).first()
    if not evidence:
        raise HTTPException(404, "Evidence not found")
    rows = db.query(CustodyRecord).filter_by(
        tenant_id=tenant, evidence_id=evidence_id
    ).order_by(CustodyRecord.id.asc()).all()
    previous_hash = GENESIS
    failures = []
    for row in rows:
        timestamp = utc_normalized(row.occurred_at).isoformat()
        body = {"tenant_id": tenant, "evidence_id": evidence_id, "actor": row.actor,
            "action": row.action, "details": row.details, "previous_hash": previous_hash,
            "occurred_at": timestamp}
        expected = sha256_hex(canonical_json(body))
        if row.previous_hash != previous_hash or row.record_hash != expected:
            failures.append(row.id)
        previous_hash = row.record_hash
    return {"evidence_id": evidence_id, "valid": not failures,
        "records_checked": len(rows), "failed_sequences": failures,
        "limitation": "Hash chaining detects accidental or unsophisticated record changes; a privileged database operator could rewrite the entire chain. External anchoring/WORM is still required."}
