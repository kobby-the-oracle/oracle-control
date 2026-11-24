from pathlib import Path\nimport hashlib
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from oracle_control.config import EVIDENCE_DIR, MAX_UPLOAD_BYTES
from oracle_control.db import get_db
from oracle_control.entities import AuditRecord, CaseRecord, EvidenceRecord
from oracle_control.security import tenant_principal
from oracle_control.evidence import sha256_hex, verify_digest

router = APIRouter(prefix="/v1/evidence", tags=["evidence"])

@router.post("", status_code=201)
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str | None = Form(default=None),
    source_system: str = Form(default="analyst-upload"),
    source_reference: str | None = Form(default=None),
    principal=Depends(tenant_principal),
    db: Session=Depends(get_db),
):
    tenant=principal["tenant_id"]
    if case_id and not db.query(CaseRecord).filter_by(id=case_id,tenant_id=tenant).first():
        raise HTTPException(404,"Case not found")
    raw=await file.read(MAX_UPLOAD_BYTES+1)
    if len(raw)>MAX_UPLOAD_BYTES: raise HTTPException(413,"Evidence exceeds configured upload limit")
    if not raw: raise HTTPException(400,"Empty evidence files are not accepted")
    evidence_id=str(uuid4())
    digest=sha256_hex(raw)
    tenant_partition=hashlib.sha256(tenant.encode("utf-8")).hexdigest()\n    target=EVIDENCE_DIR/tenant_partition/evidence_id
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(raw)
    row=EvidenceRecord(id=evidence_id,tenant_id=tenant,case_id=case_id,
        filename=Path(file.filename or "evidence.bin").name.replace("..","_")[:512],
        media_type=(file.content_type or "application/octet-stream")[:256],
        storage_path=str(target),byte_length=len(raw),sha256=digest,
        source_system=source_system[:256],source_reference=source_reference,
        collected_by=principal["subject"],metadata_json={"collection_method":"authenticated-upload"})
    db.add(row)
    db.add(AuditRecord(tenant_id=tenant,actor=principal["subject"],action="evidence.collected",
        object_type="evidence",object_id=evidence_id,details={"sha256":digest,"byte_length":len(raw)}))
    db.commit()
    return {"id":row.id,"case_id":row.case_id,"filename":row.filename,"media_type":row.media_type,
        "byte_length":row.byte_length,"sha256":row.sha256,"algorithm":"sha256",
        "collected_at":row.collected_at,"integrity_scope":"bytes received and hashed by this service"}

@router.get("")
def list_evidence(case_id: str | None=None, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    q=db.query(EvidenceRecord).filter_by(tenant_id=principal["tenant_id"])
    if case_id: q=q.filter_by(case_id=case_id)
    rows=q.order_by(EvidenceRecord.collected_at.desc()).all()
    return [{"id":r.id,"case_id":r.case_id,"filename":r.filename,"media_type":r.media_type,
        "byte_length":r.byte_length,"sha256":r.sha256,"collected_at":r.collected_at} for r in rows]

@router.post("/{evidence_id}/verify")
def verify_evidence(evidence_id:str, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    row=db.query(EvidenceRecord).filter_by(id=evidence_id,tenant_id=principal["tenant_id"]).first()
    if not row: raise HTTPException(404,"Evidence not found")
    path=Path(row.storage_path)
    if not path.is_file(): raise HTTPException(410,"Stored evidence bytes are unavailable")
    raw=path.read_bytes()
    valid=len(raw)==row.byte_length and verify_digest(raw,row.sha256)
    db.add(AuditRecord(tenant_id=row.tenant_id,actor=principal["subject"],action="evidence.verified",
        object_type="evidence",object_id=row.id,details={"valid":valid,"sha256":row.sha256}))
    db.commit()
    return {"evidence_id":row.id,"valid":valid,"algorithm":"sha256","expected_sha256":row.sha256,
        "actual_sha256":sha256_hex(raw),"byte_length":len(raw),
        "limitation":"Digest verification establishes integrity since collection, not source authenticity or collection completeness."}

@router.get("/{evidence_id}/download")
def download_evidence(evidence_id:str, principal=Depends(tenant_principal), db:Session=Depends(get_db)):
    row=db.query(EvidenceRecord).filter_by(id=evidence_id,tenant_id=principal["tenant_id"]).first()
    if not row: raise HTTPException(404,"Evidence not found")
    path=Path(row.storage_path)
    if not path.is_file(): raise HTTPException(410,"Stored evidence bytes are unavailable")
    db.add(AuditRecord(tenant_id=row.tenant_id,actor=principal["subject"],action="evidence.downloaded",
        object_type="evidence",object_id=row.id,details={"sha256":row.sha256}))
    db.commit()
    return FileResponse(path,filename=row.filename,media_type=row.media_type)
