from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from oracle_control.db import get_db
from oracle_control.entities import AuditRecord, CaseRecord, EvidenceRecord, LegalHoldRecord
from oracle_control.security import require_roles

router = APIRouter(prefix="/v1/legal-holds", tags=["retention and legal holds"])


class HoldCreate(BaseModel):
    case_id: str
    evidence_id: str | None = None
    reason: str = Field(min_length=5, max_length=4000)


@router.post("", status_code=201)
def create_hold(body: HoldCreate, principal=Depends(require_roles("analyst", "admin")), db: Session = Depends(get_db)):
    tenant = principal["tenant_id"]
    case = db.query(CaseRecord).filter_by(id=body.case_id, tenant_id=tenant).first()
    if not case:
        raise HTTPException(404, "Case not found")
    if body.evidence_id and not db.query(EvidenceRecord).filter_by(
        id=body.evidence_id, tenant_id=tenant
    ).first():
        raise HTTPException(404, "Evidence not found")
    row = LegalHoldRecord(id=str(uuid4()), tenant_id=tenant, case_id=body.case_id,
        evidence_id=body.evidence_id, reason=body.reason, placed_by=principal["subject"])
    db.add(row)
    db.add(AuditRecord(tenant_id=tenant, actor=principal["subject"], action="legal_hold.placed",
        object_type="legal_hold", object_id=row.id, details={"case_id":body.case_id,"evidence_id":body.evidence_id}))
    db.commit()
    return {"id":row.id,"case_id":row.case_id,"evidence_id":row.evidence_id,
        "reason":row.reason,"status":row.status,"created_at":row.created_at}


@router.get("")
def list_holds(case_id: str | None = None, principal=Depends(require_roles("analyst", "auditor", "admin")), db: Session = Depends(get_db)):
    q=db.query(LegalHoldRecord).filter_by(tenant_id=principal["tenant_id"])
    if case_id:q=q.filter_by(case_id=case_id)
    rows=q.order_by(LegalHoldRecord.created_at.desc()).all()
    return [{"id":r.id,"case_id":r.case_id,"evidence_id":r.evidence_id,"reason":r.reason,
        "status":r.status,"placed_by":r.placed_by,"released_by":r.released_by,
        "created_at":r.created_at,"released_at":r.released_at} for r in rows]


@router.post("/{hold_id}/release")
def release_hold(hold_id: str, principal=Depends(require_roles("analyst", "admin")), db: Session = Depends(get_db)):
    row=db.query(LegalHoldRecord).filter_by(id=hold_id,tenant_id=principal["tenant_id"]).first()
    if not row:raise HTTPException(404,"Legal hold not found")
    if row.status!="active":raise HTTPException(409,"Legal hold is not active")
    row.status="released";row.released_by=principal["subject"];row.released_at=datetime.now(timezone.utc)
    db.add(AuditRecord(tenant_id=row.tenant_id,actor=principal["subject"],action="legal_hold.released",
        object_type="legal_hold",object_id=row.id,details={"case_id":row.case_id,"evidence_id":row.evidence_id}))
    db.commit()
    return {"id":row.id,"status":row.status,"released_at":row.released_at}
