from uuid import uuid4\nimport io, json, zipfile\nfrom pathlib import Path\nfrom fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from oracle_control.db import get_db
from oracle_control.entities import AuditRecord, CaseRecord, EvidenceRecord, FindingRecord
from oracle_control.security import tenant_principal

router = APIRouter(prefix="/v1/cases", tags=["investigations"])

class CaseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    description: str = ""
    severity: str = "medium"

class FindingCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    statement: str = Field(min_length=3)
    confidence: str = "unknown"
    evidence_ids: list[str] = Field(default_factory=list)

@router.post("", status_code=201)
def create_case(body: CaseCreate, principal=Depends(tenant_principal), db: Session=Depends(get_db)):
    if body.severity not in {"critical","high","medium","low"}:
        raise HTTPException(422, "Invalid severity")
    row = CaseRecord(id=str(uuid4()), tenant_id=principal["tenant_id"], title=body.title,
        description=body.description, severity=body.severity, created_by=principal["subject"])
    db.add(row)
    db.add(AuditRecord(tenant_id=row.tenant_id, actor=principal["subject"], action="case.created",
        object_type="case", object_id=row.id, details={"severity": row.severity}))
    db.commit()
    return {"id":row.id,"title":row.title,"description":row.description,"severity":row.severity,"status":row.status,"created_at":row.created_at}

@router.get("")
def list_cases(principal=Depends(tenant_principal), db: Session=Depends(get_db)):
    rows=db.query(CaseRecord).filter_by(tenant_id=principal["tenant_id"]).order_by(CaseRecord.created_at.desc()).all()
    return [{"id":r.id,"title":r.title,"severity":r.severity,"status":r.status,"created_at":r.created_at} for r in rows]

@router.get("/{case_id}")
def get_case(case_id:str, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    row=db.query(CaseRecord).filter_by(id=case_id,tenant_id=principal["tenant_id"]).first()
    if not row: raise HTTPException(404,"Case not found")
    return {"id":row.id,"title":row.title,"description":row.description,"severity":row.severity,"status":row.status,
        "created_at":row.created_at,"findings":[{"id":f.id,"title":f.title,"statement":f.statement,"confidence":f.confidence,"evidence_ids":f.evidence_ids} for f in row.findings]}

@router.post("/{case_id}/findings",status_code=201)
def add_finding(case_id:str, body:FindingCreate, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    tenant=principal["tenant_id"]
    case=db.query(CaseRecord).filter_by(id=case_id,tenant_id=tenant).first()
    if not case: raise HTTPException(404,"Case not found")
    if body.confidence not in {"directly_observed","correlated","inferred","unknown"}: raise HTTPException(422,"Invalid confidence")
    if body.evidence_ids:
        found={e.id for e in db.query(EvidenceRecord).filter(
            EvidenceRecord.tenant_id==tenant,
            EvidenceRecord.id.in_(body.evidence_ids)).all()}
        if found != set(body.evidence_ids): raise HTTPException(422,"Evidence reference missing or belongs to another tenant")
    row=FindingRecord(id=str(uuid4()),case_id=case_id,tenant_id=tenant,title=body.title,statement=body.statement,
        confidence=body.confidence,evidence_ids=body.evidence_ids)
    db.add(row)
    db.add(AuditRecord(tenant_id=tenant,actor=principal["subject"],action="finding.created",object_type="finding",object_id=row.id,details={"case_id":case_id}))
    db.commit()
    return {"id":row.id,"case_id":case_id,"title":row.title,"confidence":row.confidence,"evidence_ids":row.evidence_ids}

@router.patch("/{case_id}/status")
def update_case_status(case_id:str, status:str, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    if status not in {"open","investigating","contained","resolved","closed"}:
        raise HTTPException(422,"Invalid case status")
    row=db.query(CaseRecord).filter_by(id=case_id,tenant_id=principal["tenant_id"]).first()
    if not row: raise HTTPException(404,"Case not found")
    previous=row.status
    row.status=status
    db.add(AuditRecord(tenant_id=row.tenant_id,actor=principal["subject"],action="case.status_changed",
        object_type="case",object_id=row.id,details={"from":previous,"to":status}))
    db.commit()
    return {"id":row.id,"status":row.status}

@router.get("/{case_id}/export")
def export_case(case_id:str, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    tenant=principal["tenant_id"]
    case=db.query(CaseRecord).filter_by(id=case_id,tenant_id=tenant).first()
    if not case: raise HTTPException(404,"Case not found")
    evidence=db.query(EvidenceRecord).filter_by(tenant_id=tenant,case_id=case_id).all()
    findings=db.query(FindingRecord).filter_by(tenant_id=tenant,case_id=case_id).all()
    manifest={"format":"oracle-control-case-export-v1","case_id":case.id,"tenant_id":tenant,
        "exported_at":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "integrity_note":"SHA-256 verifies included bytes against collection digests; it does not prove source authenticity or collection completeness.",
        "evidence":[]}
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("case.json",json.dumps({"id":case.id,"title":case.title,"description":case.description,
            "severity":case.severity,"status":case.status,"created_at":case.created_at.isoformat()},default=str,indent=2))
        archive.writestr("findings.json",json.dumps([{"id":f.id,"title":f.title,"statement":f.statement,
            "confidence":f.confidence,"evidence_ids":f.evidence_ids} for f in findings],indent=2))
        for item in evidence:
            path=Path(item.storage_path)
            if not path.is_file(): raise HTTPException(410,f"Evidence bytes unavailable: {item.id}")
            raw=path.read_bytes()
            from oracle_control.evidence import sha256_hex
            actual=sha256_hex(raw)
            if len(raw)!=item.byte_length or actual!=item.sha256:
                raise HTTPException(409,f"Evidence integrity check failed: {item.id}")
            archive.writestr(f"evidence/{item.id}/{item.filename}",raw)
            manifest["evidence"].append({"id":item.id,"filename":item.filename,"path":f"evidence/{item.id}/{item.filename}",
                "sha256":item.sha256,"byte_length":item.byte_length,"source_system":item.source_system,
                "source_reference":item.source_reference,"collected_by":item.collected_by,"collected_at":item.collected_at.isoformat()})
        archive.writestr("manifest.json",json.dumps(manifest,indent=2))
    db.add(AuditRecord(tenant_id=tenant,actor=principal["subject"],action="case.exported",
        object_type="case",object_id=case_id,details={"evidence_count":len(evidence),"finding_count":len(findings)}))
    db.commit()
    stream.seek(0)
    return StreamingResponse(stream,media_type="application/zip",
        headers={"Content-Disposition":f'attachment; filename="oracle-control-{case_id}.zip"'})
