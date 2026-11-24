import pytest
from fastapi import HTTPException

from oracle_control.security import _principal_from_claims, _roles_from_claims
from oracle_control.connectors.cloud_saas import (
    AzureActivityLogAdapter,
    GitHubAuditLogAdapter,
    GoogleCloudAuditLogAdapter,
)


def test_oidc_claim_mapping_extracts_tenant_subject_and_roles():
    principal = _principal_from_claims({
        "sub": "analyst-17",
        "tenant_id": "tenant-abc",
        "roles": ["analyst", "auditor"],
    })
    assert principal == {
        "tenant_id": "tenant-abc",
        "subject": "analyst-17",
        "roles": ["analyst", "auditor"],
        "auth_method": "oidc",
    }


def test_oidc_claim_mapping_rejects_missing_tenant():
    with pytest.raises(HTTPException) as error:
        _principal_from_claims({"sub": "analyst-17", "roles": ["analyst"]})
    assert error.value.status_code == 403


def test_oidc_roles_claim_supports_nested_role_object():
    assert _roles_from_claims({"roles": {"roles": ["admin"]}}) == ["admin"]


def test_azure_activity_adapter_omits_claims_and_parses_source_fields():
    event = AzureActivityLogAdapter().parse({
        "eventDataId": "azure-event-1",
        "eventTimestamp": "2026-11-24T02:00:00Z",
        "operationName": {"value": "Microsoft.Storage/storageAccounts/listKeys/action"},
        "caller": "service-principal-7",
        "resourceId": "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/data",
        "claims": {"access_token": "must-not-be-retained", "upn": "person@example.test"},
        "status": {"value": "Succeeded"},
    }, tenant_id="tenant-a")
    assert event.actor_id == "service-principal-7"
    assert event.payload["operation"].startswith("Microsoft.Storage")
    assert "claims" not in event.payload
    assert "access_token" not in str(event.payload)


def test_google_audit_adapter_omits_request_payload():
    event = GoogleCloudAuditLogAdapter().parse({
        "insertId": "gcp-event-9",
        "timestamp": "2026-11-24T02:00:00Z",
        "protoPayload": {
            "methodName": "storage.objects.get",
            "serviceName": "storage.googleapis.com",
            "resourceName": "projects/_/buckets/demo/objects/file",
            "authenticationInfo": {"principalEmail": "agent@example.test"},
            "request": {"secret": "must-not-be-copied"},
            "requestMetadata": {"callerIp": "192.0.2.1"},
        },
        "resource": {"type": "gcs_bucket", "labels": {"project_id": "demo"}},
    }, tenant_id="tenant-a")
    assert event.actor_id == "agent@example.test"
    assert event.resource_id.endswith("/file")
    assert "request" not in event.payload
    assert "secret" not in str(event.payload)


def test_github_audit_adapter_requires_stable_source_id():
    adapter = GitHubAuditLogAdapter()
    with pytest.raises(ValueError):
        adapter.parse({"action": "repo.download_zip"}, tenant_id="tenant-a")
    event = adapter.parse({
        "_document_id": "github-audit-22",
        "@timestamp": "2026-11-24T02:00:00Z",
        "action": "repo.access",
        "actor": "automation-bot",
        "repo": "example/private",
    }, tenant_id="tenant-a")
    assert event.source.event_id == "github-audit-22"
    assert event.actor_id == "automation-bot"
    assert event.resource_id == "example/private"

def test_oidc_signature_issuer_audience_and_expiry_are_verified(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    import oracle_control.security as security

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    class FakeJwks:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=private_key.public_key())

    monkeypatch.setattr(security, "OIDC_ISSUER", "https://identity.example.test/")
    monkeypatch.setattr(security, "OIDC_AUDIENCE", "oracle-control-api")
    monkeypatch.setattr(security, "OIDC_JWKS_URL", "https://identity.example.test/keys")
    monkeypatch.setattr(security, "_jwks_client", lambda _url: FakeJwks())
    now = datetime.now(timezone.utc)
    claims = {
        "iss": "https://identity.example.test/",
        "aud": "oracle-control-api",
        "sub": "user-1",
        "tenant_id": "tenant-a",
        "roles": ["analyst"],
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    principal = security._authenticate_oidc(token)
    assert principal["tenant_id"] == "tenant-a"
    assert principal["subject"] == "user-1"
    assert principal["roles"] == ["analyst"]

    invalid = dict(claims, iss="https://attacker.example.test/")
    invalid_token = jwt.encode(invalid, private_key, algorithm="RS256")
    with pytest.raises(HTTPException) as error:
        security._authenticate_oidc(invalid_token)
    assert error.value.status_code == 401
