import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from oracle_control.config import EVIDENCE_DIR, MAX_UPLOAD_BYTES, STORAGE_BACKEND
from oracle_control.custody import append_custody
from oracle_control.db import get_db
from oracle_control.entities import AuditRecord, CaseRecord, EvidenceRecord
from oracle_control.evidence import sha256_hex, verify_digest
from oracle_control.security import require_roles
from oracle_control.storage import EvidenceStorageError, read_evidence, store_evidence

router = APIRouter(prefix="/v1/evidence", tags=["evidence"])


@router.post("", status_code=201)
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str | None = Form(default=None),
    source_system: str = Form(default="analyst-upload"),
    source_reference: str | None = Form(default=None),
    principal=Depends(require_roles('analyst', 'collector', 'admin')),
    db: Session = Depends(get_db),
):
    tenant = principal["tenant_id"]
    if case_id and not db.query(CaseRecord).filter_by(id=case_id, tenant_id=tenant).first():
        raise HTTPException(404, "Case not found")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Evidence exceeds configured upload limit")
    if not raw:
        raise HTTPException(400, "Empty evidence files are not accepted")
    evidence_id = str(uuid4())
    digest = sha256_hex(raw)
    tenant_partition = hashlib.sha256(tenant.encode("utf-8")).hexdigest()
    object_key = f"{tenant_partition}/{evidence_id}"
    filename = Path(file.filename or "evidence.bin").name.replace("..", "_")[:512]
    try:
        storage_path = store_evidence(object_key, raw, file.content_type or "application/octet-stream")
    except EvidenceStorageError as exc:
        raise HTTPException(502, str(exc)) from exc
    row = EvidenceRecord(
        id=evidence_id, tenant_id=tenant, case_id=case_id, filename=filename,
        media_type=(file.content_type or "application/octet-stream")[:256],
        storage_path=storage_path, byte_length=len(raw), sha256=digest,
        source_system=source_system[:256], source_reference=source_reference,
        collected_by=principal["subject"],
        metadata_json={"collection_method": "authenticated-upload", "storage_backend": STORAGE_BACKEND},
    )
    db.add(row)
    db.flush()
    append_custody(db, tenant_id=tenant, evidence_id=evidence_id, actor=principal["subject"], action="evidence.collected", details={"sha256":digest,"byte_length":len(raw)})
    db.add(AuditRecord(
        tenant_id=tenant, actor=principal["subject"], action="evidence.collected",
        object_type="evidence", object_id=evidence_id,
        details={"sha256": digest, "byte_length": len(raw)},
    ))
    db.commit()
    return {
        "id": row.id, "case_id": row.case_id, "filename": row.filename,
        "media_type": row.media_type, "byte_length": row.byte_length,
        "sha256": row.sha256, "algorithm": "sha256", "collected_at": row.collected_at,
        "integrity_scope": "bytes received and hashed by this service",
    }


@router.get("")
def list_evidence(
    case_id: str | None = None, principal=Depends(require_roles('analyst', 'auditor', 'admin')), db: Session = Depends(get_db)
):
    q = db.query(EvidenceRecord).filter_by(tenant_id=principal["tenant_id"])
    if case_id:
        q = q.filter_by(case_id=case_id)
    rows = q.order_by(EvidenceRecord.collected_at.desc()).all()
    return [
        {"id": r.id, "case_id": r.case_id, "filename": r.filename, "media_type": r.media_type,
         "byte_length": r.byte_length, "sha256": r.sha256, "collected_at": r.collected_at}
        for r in rows
    ]


@router.post("/{evidence_id}/verify")
def verify_evidence(
    evidence_id: str, principal=Depends(require_roles('analyst', 'auditor', 'admin')), db: Session = Depends(get_db)
):
    row = db.query(EvidenceRecord).filter_by(
        id=evidence_id, tenant_id=principal["tenant_id"]
    ).first()
    if not row:
        raise HTTPException(404, "Evidence not found")
    try:
        raw = read_evidence(row.storage_path)
    except FileNotFoundError as exc:
        raise HTTPException(410, "Stored evidence bytes are unavailable") from exc
    except EvidenceStorageError as exc:
        raise HTTPException(502, str(exc)) from exc
    valid = len(raw) == row.byte_length and verify_digest(raw, row.sha256)
    append_custody(db, tenant_id=row.tenant_id, evidence_id=row.id, actor=principal["subject"], action="evidence.verified", details={"valid":valid,"sha256":row.sha256})
    db.add(AuditRecord(
        tenant_id=row.tenant_id, actor=principal["subject"], action="evidence.verified",
        object_type="evidence", object_id=row.id, details={"valid": valid, "sha256": row.sha256},
    ))
    db.commit()
    return {
        "evidence_id": row.id, "valid": valid, "algorithm": "sha256",
        "expected_sha256": row.sha256, "actual_sha256": sha256_hex(raw),
        "byte_length": len(raw),
        "limitation": "Digest verification establishes integrity since collection, not source authenticity or collection completeness.",
    }


@router.get("/{evidence_id}/download")
def download_evidence(
    evidence_id: str, principal=Depends(require_roles('analyst', 'auditor', 'admin')), db: Session = Depends(get_db)
):
    row = db.query(EvidenceRecord).filter_by(
        id=evidence_id, tenant_id=principal["tenant_id"]
    ).first()
    if not row:
        raise HTTPException(404, "Evidence not found")
    try:
        current_bytes = read_evidence(row.storage_path)
    except FileNotFoundError as exc:
        raise HTTPException(410, "Stored evidence bytes are unavailable") from exc
    except EvidenceStorageError as exc:
        raise HTTPException(502, str(exc)) from exc
    if len(current_bytes) != row.byte_length or not verify_digest(current_bytes, row.sha256):
        raise HTTPException(409, "Evidence integrity verification failed; download blocked")
    append_custody(db, tenant_id=row.tenant_id, evidence_id=row.id, actor=principal["subject"], action="evidence.downloaded", details={"sha256":row.sha256})
    db.add(AuditRecord(
        tenant_id=row.tenant_id, actor=principal["subject"], action="evidence.downloaded",
        object_type="evidence", object_id=row.id, details={"sha256": row.sha256},
    ))
    db.commit()
    if row.storage_path.startswith("supabase://"):
        from urllib.parse import quote
        return Response(
            content=current_bytes, media_type=row.media_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(row.filename)}"},
        )
    return FileResponse(Path(row.storage_path), filename=row.filename, media_type=row.media_type)
