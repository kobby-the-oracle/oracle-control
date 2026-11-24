import secrets
from typing import Any

from fastapi import Depends, Header, HTTPException

from oracle_control.config import ALLOW_DEV_TENANT_HEADER, API_KEYS


def tenant_principal(
    x_api_key: str | None = Header(default=None),
    x_dev_tenant: str | None = Header(default=None),
) -> dict[str, Any]:
    # API-key mapping is a bootstrap adapter. Production deployments should use OIDC/SAML
    # and workload identity; never enable the development tenant header in production.
    if x_api_key:
        for key, entry in API_KEYS.items():
            if secrets.compare_digest(x_api_key, key):
                if isinstance(entry, str):
                    return {"tenant_id": entry, "subject": "api-key", "roles": ["analyst", "collector"]}
                if isinstance(entry, dict) and entry.get("tenant_id"):
                    return {
                        "tenant_id": str(entry["tenant_id"]),
                        "subject": str(entry.get("subject", "api-key")),
                        "roles": list(entry.get("roles", [])),
                    }
    if ALLOW_DEV_TENANT_HEADER and x_dev_tenant:
        return {"tenant_id": x_dev_tenant, "subject": "development-header", "roles": ["analyst", "collector"]}
    raise HTTPException(status_code=401, detail="Valid API key required")


def require_roles(*allowed_roles: str):
    def role_dependency(principal=Depends(tenant_principal)):
        if not set(principal.get("roles", [])).intersection(allowed_roles):
            raise HTTPException(status_code=403, detail="Insufficient role for this operation")
        return principal
    return role_dependency
