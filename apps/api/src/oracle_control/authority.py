from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from oracle_control.db import get_db
from oracle_control.entities import ApprovalRecord, AuditRecord, AuthorityRecord, EvidenceRecord
from oracle_control.security import tenant_principal

router=APIRouter(prefix="/v1/authority",tags=["authority intelligence"])

class AuthorityInput(BaseModel):
    agent_id:str=Field(min_length=1,max_length=256)
    principal_id:str=Field(min_length=1,max_length=256)
    permission:str=Field(min_length=1,max_length=256)
    resource_scope:str=Field(min_length=1,max_length=1024)
    decision:str="granted"
    source_system:str="analyst-recorded"
    approval_reference:str|None=None
    evidence_ids:list[str]=Field(default_factory=list)

class ApprovalInput(BaseModel):
    agent_id:str
    approver_id:str
    action:str
    resource_scope:str
    decision:str
    source_system:str="analyst-recorded"
    source_reference:str|None=None
    evidence_ids:list[str]=Field(default_factory=list)

def validate_evidence(db,tenant,ids):
    if not ids:return
    found={r.id for r in db.query(EvidenceRecord).filter(EvidenceRecord.tenant_id==tenant,EvidenceRecord.id.in_(ids)).all()}
    if found!=set(ids):raise HTTPException(422,"Evidence reference missing or belongs to another tenant")

@router.post("/records",status_code=201)
def record_authority(body:AuthorityInput,principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    if body.decision not in {"granted","denied","revoked","unknown"}:raise HTTPException(422,"Invalid authority decision")
    tenant=principal["tenant_id"];validate_evidence(db,tenant,body.evidence_ids)
    row=AuthorityRecord(id=str(uuid4()),tenant_id=tenant,agent_id=body.agent_id,principal_id=body.principal_id,
        permission=body.permission,resource_scope=body.resource_scope,decision=body.decision,
        source_system=body.source_system,approval_reference=body.approval_reference,evidence_ids=body.evidence_ids)
    db.add(row);db.add(AuditRecord(tenant_id=tenant,actor=principal["subject"],action="authority.recorded",
        object_type="authority",object_id=row.id,details={"agent_id":body.agent_id,"decision":body.decision}))
    db.commit()
    return {"id":row.id,"agent_id":row.agent_id,"principal_id":row.principal_id,"permission":row.permission,
        "resource_scope":row.resource_scope,"decision":row.decision,"evidence_ids":row.evidence_ids}

@router.get("/records")
def list_authority(agent_id:str|None=None,principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    q=db.query(AuthorityRecord).filter_by(tenant_id=principal["tenant_id"])
    if agent_id:q=q.filter_by(agent_id=agent_id)
    return [{"id":r.id,"agent_id":r.agent_id,"principal_id":r.principal_id,"permission":r.permission,
        "resource_scope":r.resource_scope,"decision":r.decision,"source_system":r.source_system,
        "approval_reference":r.approval_reference,"valid_from":r.valid_from,"valid_until":r.valid_until,
        "evidence_ids":r.evidence_ids} for r in q.order_by(AuthorityRecord.created_at.desc()).all()]

@router.post("/approvals",status_code=201)
def record_approval(body:ApprovalInput,principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    if body.decision not in {"approved","denied","withdrawn","unknown"}:raise HTTPException(422,"Invalid approval decision")
    tenant=principal["tenant_id"];validate_evidence(db,tenant,body.evidence_ids)
    row=ApprovalRecord(id=str(uuid4()),tenant_id=tenant,agent_id=body.agent_id,approver_id=body.approver_id,
        action=body.action,resource_scope=body.resource_scope,decision=body.decision,
        source_system=body.source_system,source_reference=body.source_reference,evidence_ids=body.evidence_ids)
    db.add(row);db.add(AuditRecord(tenant_id=tenant,actor=principal["subject"],action="approval.recorded",
        object_type="approval",object_id=row.id,details={"agent_id":body.agent_id,"decision":body.decision}))
    db.commit()
    return {"id":row.id,"agent_id":row.agent_id,"approver_id":row.approver_id,"action":row.action,
        "resource_scope":row.resource_scope,"decision":row.decision,"evidence_ids":row.evidence_ids}

@router.get("/approvals")
def list_approvals(agent_id:str|None=None,principal=Depends(tenant_principal),db:Session=Depends(get_db)):
    q=db.query(ApprovalRecord).filter_by(tenant_id=principal["tenant_id"])
    if agent_id:q=q.filter_by(agent_id=agent_id)
    return [{"id":r.id,"agent_id":r.agent_id,"approver_id":r.approver_id,"action":r.action,
        "resource_scope":r.resource_scope,"decision":r.decision,"source_system":r.source_system,
        "source_reference":r.source_reference,"decided_at":r.decided_at,"evidence_ids":r.evidence_ids}
        for r in q.order_by(ApprovalRecord.decided_at.desc()).all()]
