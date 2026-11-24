import secrets
from fastapi import Header, HTTPException
from oracle_control.config import API_KEYS, ALLOW_DEV_TENANT_HEADER

def tenant_principal(
    x_api_key: str | None = Header(default=None),
    x_dev_tenant: str | None = Header(default=None),
) -> dict[str, str]:
    # API-key mapping is a bootstrap adapter. Production deployments should use OIDC/SAML
    # and workload identity; never enable the development tenant header in production.
    if x_api_key:
        for key, tenant in API_KEYS.items():
            if secrets.compare_digest(x_api_key, key):
                return {"tenant_id": tenant, "subject": "api-key"}
    if ALLOW_DEV_TENANT_HEADER and x_dev_tenant:
        return {"tenant_id": x_dev_tenant, "subject": "development-header"}
    raise HTTPException(status_code=401, detail="Valid API key required")
