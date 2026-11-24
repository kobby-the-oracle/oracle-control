import json
import os
from pathlib import Path

DATABASE_URL = os.getenv("ORACLE_DATABASE_URL", "sqlite:///./oracle-control-dev.db")
EVIDENCE_DIR = Path(os.getenv("ORACLE_EVIDENCE_DIR", "./var/evidence")).resolve()
MAX_UPLOAD_BYTES = int(os.getenv("ORACLE_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
API_KEYS = json.loads(os.getenv("ORACLE_API_KEYS", "{}") or "{}")
ALLOW_DEV_TENANT_HEADER = os.getenv("ORACLE_ALLOW_DEV_TENANT_HEADER", "false").lower() == "true"
AUTO_CREATE_SCHEMA = os.getenv(
    "ORACLE_AUTO_CREATE_SCHEMA", "true" if DATABASE_URL.startswith("sqlite") else "false"
).lower() == "true"
STORAGE_BACKEND = os.getenv("ORACLE_STORAGE_BACKEND", "local").lower()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_EVIDENCE_BUCKET = os.getenv("SUPABASE_EVIDENCE_BUCKET", "oracle-control-evidence")

# OIDC authorization-code flow is performed by the identity provider/client.
# The API validates signed access tokens against the configured issuer and JWKS.
OIDC_ISSUER = os.getenv("ORACLE_OIDC_ISSUER", "").rstrip("/")
OIDC_AUDIENCE = os.getenv("ORACLE_OIDC_AUDIENCE", "")
OIDC_JWKS_URL = os.getenv("ORACLE_OIDC_JWKS_URL", "")
OIDC_TENANT_CLAIM = os.getenv("ORACLE_OIDC_TENANT_CLAIM", "tenant_id")
OIDC_ROLE_CLAIM = os.getenv("ORACLE_OIDC_ROLE_CLAIM", "roles")

LLM_ENABLED = os.getenv("ORACLE_LLM_ENABLED", "false").lower() == "true"
LLM_BASE_URL = os.getenv("ORACLE_LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.getenv("ORACLE_LLM_API_KEY", "")
LLM_MODEL = os.getenv("ORACLE_LLM_MODEL", "")
LLM_TIMEOUT_SECONDS = float(os.getenv("ORACLE_LLM_TIMEOUT_SECONDS", "30"))

CORS_ORIGINS = [origin.strip() for origin in os.getenv(
    "ORACLE_CORS_ORIGINS", "http://localhost:5173,http://localhost:4173,http://localhost:8080"
).split(",") if origin.strip()]
