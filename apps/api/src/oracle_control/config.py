import json
import os
from pathlib import Path

DATABASE_URL = os.getenv("ORACLE_DATABASE_URL", "sqlite:///./oracle-control-dev.db")
EVIDENCE_DIR = Path(os.getenv("ORACLE_EVIDENCE_DIR", "./var/evidence")).resolve()
MAX_UPLOAD_BYTES = int(os.getenv("ORACLE_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
API_KEYS = json.loads(os.getenv("ORACLE_API_KEYS", "{}"))
ALLOW_DEV_TENANT_HEADER = os.getenv("ORACLE_ALLOW_DEV_TENANT_HEADER", "false").lower() == "true"

LLM_ENABLED = os.getenv("ORACLE_LLM_ENABLED", "false").lower() == "true"
LLM_BASE_URL = os.getenv("ORACLE_LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.getenv("ORACLE_LLM_API_KEY", "")
LLM_MODEL = os.getenv("ORACLE_LLM_MODEL", "")
LLM_TIMEOUT_SECONDS = float(os.getenv("ORACLE_LLM_TIMEOUT_SECONDS", "30"))
