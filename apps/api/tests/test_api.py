from fastapi.testclient import TestClient
from oracle_control.main import app, _events

client = TestClient(app)

def setup_function():
    _events.clear()

def sample_event():
    return {
        "event_id": "evt-001",
        "tenant_id": "tenant-demo",
        "source": {"system": "demo-agent", "event_id": "src-001"},
        "event_type": "tool.invoked",
        "occurred_at": "2026-11-24T01:00:00Z",
        "agent_id": "agent-7",
        "run_id": "run-42",
        "actor_id": "user-3",
        "resource_id": "bucket/customer-data",
        "relationship_confidence": "directly_observed",
        "payload": {"tool": "object.read", "result": "success"},
    }

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_ingest_and_idempotent_replay():
    event = sample_event()
    first = client.post("/v1/events", json=event)
    second = client.post("/v1/events", json=event)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["canonical_event_sha256"] == second.json()["canonical_event_sha256"]

def test_conflicting_replay_rejected():
    event = sample_event()
    assert client.post("/v1/events", json=event).status_code == 201
    event["payload"]["result"] = "different"
    assert client.post("/v1/events", json=event).status_code == 409

def test_tenant_filter():
    client.post("/v1/events", json=sample_event())
    other = sample_event()
    other["tenant_id"] = "another-tenant"
    other["event_id"] = "evt-002"
    client.post("/v1/events", json=other)
    response = client.get("/v1/events", params={"tenant_id": "tenant-demo"})
    assert response.status_code == 200
    assert len(response.json()) == 1
