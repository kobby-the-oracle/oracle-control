from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
import httpx

from oracle_control.config import (
    EVIDENCE_DIR,
    STORAGE_BACKEND,
    SUPABASE_EVIDENCE_BUCKET,
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
)
from oracle_control.db import engine
from oracle_control.security import require_roles
from oracle_control.storage import storage_auth_headers

router = APIRouter(prefix="/v1/admin/system", tags=["system administration"])


def _database_check() -> str:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        # Deliberately omit driver errors and connection details from the response.
        return "unavailable"


def _storage_check() -> str:
    if STORAGE_BACKEND == "local":
        return "ok" if EVIDENCE_DIR.is_dir() else "unavailable"
    if STORAGE_BACKEND != "supabase" or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return "misconfigured"
    try:
        response = httpx.get(
            f"{SUPABASE_URL}/storage/v1/bucket/{SUPABASE_EVIDENCE_BUCKET}",
            headers=storage_auth_headers(),
            timeout=httpx.Timeout(5.0, connect=3.0),
        )
        return "ok" if response.status_code == 200 else "unavailable"
    except httpx.HTTPError:
        return "unavailable"


@router.get("/readiness")
def system_readiness(
    response: Response,
    principal=Depends(require_roles("admin")),
):
    database = _database_check()
    storage = _storage_check()
    ready = database == "ok" and storage == "ok"
    if not ready:
        response.status_code = 503
    return {
        "status": "ready" if ready else "degraded",
        "checks": {
            "database": database,
            "evidence_storage": storage,
        },
        "note": "Connectivity checks only; this does not certify security, backup, retention, or production readiness.",
    }
