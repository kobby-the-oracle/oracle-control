import secrets
from functools import lru_cache
from typing import Any

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient

from oracle_control.config import (
    ALLOW_DEV_TENANT_HEADER,
    API_KEYS,
    OIDC_AUDIENCE,
    OIDC_ISSUER,
    OIDC_JWKS_URL,
    OIDC_ROLE_CLAIM,
    OIDC_TENANT_CLAIM,
)

@lru_cache(maxsize=4)
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_jwk_set=True, lifespan=300, timeout=5)


def _roles_from_claims(claims: dict[str, Any]) -> list[str]:
    value: Any = claims.get(OIDC_ROLE_CLAIM, claims.get("roles", []))
    if isinstance(value, dict):
        value = value.get("roles", [])
    if not isinstance(value, list):
        return []
    return [str(role) for role in value if isinstance(role, (str, int))]


def _principal_from_claims(claims: dict[str, Any]) -> dict[str, Any]:
    tenant = claims.get(OIDC_TENANT_CLAIM) or claims.get("tenant_id") or claims.get("org_id")
    subject = claims.get("sub")
    if not tenant or not subject:
        raise HTTPException(status_code=403, detail="Token is missing required tenant or subject claim")
    return {
        "tenant_id": str(tenant),
        "subject": str(subject),
        "roles": _roles_from_claims(claims),
        "auth_method": "oidc",
    }


def _authenticate_oidc(token: str) -> dict[str, Any]:
    if not (OIDC_ISSUER and OIDC_AUDIENCE and OIDC_JWKS_URL):
        raise HTTPException(status_code=503, detail="OIDC is not fully configured")
    try:
        signing_key = _jwks_client(OIDC_JWKS_URL).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            issuer=OIDC_ISSUER,
            audience=OIDC_AUDIENCE,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            leeway=30,
        )
        return _principal_from_claims(claims)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired bearer token") from exc


def tenant_principal(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
    x_dev_tenant: str | None = Header(default=None),
) -> dict[str, Any]:
    # Prefer signed OIDC access tokens when supplied. Never accept unsigned or
    # algorithm-selected tokens. API keys remain a bootstrap/service-account path.
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="Bearer token required")
        return _authenticate_oidc(token)

    if x_api_key:
        for key, entry in API_KEYS.items():
            if secrets.compare_digest(x_api_key, key):
                if isinstance(entry, str):
                    return {
                        "tenant_id": entry, "subject": "api-key",
                        "roles": ["analyst", "collector"], "auth_method": "api_key",
                    }
                if isinstance(entry, dict) and entry.get("tenant_id"):
                    return {
                        "tenant_id": str(entry["tenant_id"]),
                        "subject": str(entry.get("subject", "api-key")),
                        "roles": list(entry.get("roles", [])),
                        "auth_method": "api_key",
                    }
    if ALLOW_DEV_TENANT_HEADER and x_dev_tenant:
        return {
            "tenant_id": x_dev_tenant, "subject": "development-header",
            "roles": ["analyst", "collector"], "auth_method": "development",
        }
    # Missing credentials are always an authentication failure. A supplied bearer
    # token with missing OIDC configuration is reported separately as 503 above.
    raise HTTPException(status_code=401, detail="Valid bearer token or API key required")


def require_roles(*allowed_roles: str):
    def role_dependency(principal=Depends(tenant_principal)):
        if not set(principal.get("roles", [])).intersection(allowed_roles):
            raise HTTPException(status_code=403, detail="Insufficient role for this operation")
        return principal
    return role_dependency
