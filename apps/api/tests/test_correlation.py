from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from oracle_control.db import Base, get_db
from oracle_control.main import app


@pytest.fixture()
def client(monkeypatch):
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    import oracle_control.security as security
    monkeypatch.setattr(security, "API_KEYS", {
        "test-secret": {"tenant_id": "tenant-demo", "subject": "test-analyst",
                        "roles": ["admin", "analyst", "collector", "auditor"]}
    })
    with TestClient(app) as test_client:
        test_client.headers.update({"X-API-Key": "test-secret"})
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def make_event(event_id, agent_id, run_id, occurred_at, *, parent_agent_id=None,
               parent_run_id=None, session_id="session-1"):
    return {
        "event_id": event_id,
        "tenant_id": "tenant-demo",
        "source": {"system": "test-source", "event_id": f"source-{event_id}"},
        "event_type": "tool.invoked",
        "occurred_at": occurred_at.isoformat(),
        "agent_id": agent_id,
        "run_id": run_id,
        "session_id": session_id,
        "parent_agent_id": parent_agent_id,
        "parent_run_id": parent_run_id,
        "actor_id": "service-account",
        "resource_id": "bucket/a/file.txt",
        "relationship_confidence": "directly_observed",
        "payload": {"tool": "s3:GetObject"},
    }


def test_timeline_correlates_parent_child_runs_and_evaluates_authority(client):
    case = client.post("/v1/cases", json={
        "title": "Cross-agent investigation",
        "agent_ids": ["agent-child"],
        "severity": "high",
    }).json()
    authority = client.post("/v1/authority/records", json={
        "agent_id": "agent-child",
        "principal_id": "role-research",
        "permission": "s3:GetObject",
        "resource_scope": "bucket/a",
        "decision": "granted",
        "source_system": "test-iam",
    })
    assert authority.status_code == 201

    timestamp = datetime.now(timezone.utc) + timedelta(minutes=2)
    parent = client.post("/v1/events", json=make_event(
        "parent-event", "agent-parent", "run-parent", timestamp,
        session_id="session-1",
    ))
    child = client.post("/v1/events", json=make_event(
        "child-event", "agent-child", "run-child", timestamp + timedelta(seconds=2),
        parent_agent_id="agent-parent", parent_run_id="run-parent",
        session_id="session-1",
    ))
    assert parent.status_code == 201
    assert child.status_code == 201

    response = client.get(f"/v1/investigations/cases/{case['id']}/timeline")
    assert response.status_code == 200
    result = response.json()
    assert {item["event_id"] for item in result["events"]} == {"parent-event", "child-event"}
    assert any(edge["relationship"] == "declared_parent_run" for edge in result["relationships"])
    child_item = next(item for item in result["events"] if item["event_id"] == "child-event")
    assert child_item["authority_context"]["status"] == "matching_authority_record"
    assert child_item["authority_context"]["records"][0]["match"] == "matching_grant"
    assert result["collection_limitations"]


def test_timeline_is_tenant_scoped(client):
    case = client.post("/v1/cases", json={
        "title": "Tenant boundary case", "agent_ids": ["agent-private"]
    }).json()
    import oracle_control.security as security
    security.API_KEYS["other-secret"] = {
        "tenant_id": "other-tenant", "subject": "other-user", "roles": ["admin", "analyst"]
    }
    other = TestClient(app)
    response = other.get(
        f"/v1/investigations/cases/{case['id']}/timeline",
        headers={"X-API-Key": "other-secret"},
    )
    assert response.status_code == 404
