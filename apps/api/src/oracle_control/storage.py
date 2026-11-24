"""Evidence object storage backends.

Local filesystem storage is for development. Supabase Storage is private object storage,
not WORM storage and not an object-lock service.
"""
from pathlib import Path
from urllib.parse import quote

import httpx

from oracle_control.config import (
    EVIDENCE_DIR, STORAGE_BACKEND, SUPABASE_EVIDENCE_BUCKET,
    SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL,
)


class EvidenceStorageError(RuntimeError):
    pass


def storage_auth_headers() -> dict[str, str]:
    """Build Storage API headers for legacy JWT and new opaque secret keys."""
    headers = {"apikey": SUPABASE_SERVICE_ROLE_KEY}
    # sb_secret_ keys are opaque API keys, not JWTs; do not send them as Bearer tokens.
    if not SUPABASE_SERVICE_ROLE_KEY.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    return headers


def _storage_url(key: str) -> str:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise EvidenceStorageError("Supabase Storage is selected but server credentials are not configured")
    bucket = quote(SUPABASE_EVIDENCE_BUCKET, safe="")
    object_key = quote(key, safe="/")
    return f"{SUPABASE_URL}/storage/v1/object/{bucket}/{object_key}"


def store_evidence(key: str, raw: bytes, media_type: str) -> str:
    if STORAGE_BACKEND == "supabase":
        try:
            response = httpx.post(
                _storage_url(key), content=raw,
                headers={**storage_auth_headers(),
                    "Content-Type": media_type or "application/octet-stream",
                    "x-upsert": "false",
                }, timeout=60.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EvidenceStorageError("Supabase evidence upload failed") from exc
        return f"supabase://{key}"

    target = EVIDENCE_DIR / key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return str(target)


def read_evidence(storage_path: str) -> bytes:
    if storage_path.startswith("supabase://"):
        key = storage_path.removeprefix("supabase://")
        try:
            response = httpx.get(
                _storage_url(key),
                headers=storage_auth_headers(), timeout=60.0,
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as exc:
            raise EvidenceStorageError("Supabase evidence download failed") from exc

    path = Path(storage_path)
    if not path.is_file():
        raise FileNotFoundError(storage_path)
    return path.read_bytes()
