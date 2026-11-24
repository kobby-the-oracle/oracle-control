from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from oracle_control.evidence import event_digests, verify_digest
from oracle_control.models import AgentEventIn, StoredEvent

app = FastAPI(
    title="ORACLE CONTROL API",
    version="0.1.0",
    description="Evidence-centred AI incident investigation. Development scaffold; not production-hardened.",
)

# Volatile development-only storage. Replace with tenant-scoped durable storage before deployment.
_events: dict[tuple[str, str], StoredEvent] = {}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "oracle-control-api"}

@app.post("/v1/events", response_model=StoredEvent, status_code=201)
def ingest_event(event: AgentEventIn) -> StoredEvent:
    key = (event.tenant_id, event.event_id)
    event_dict = event.model_dump(mode="json")
    payload_digest, event_digest = event_digests(event_dict)
    existing = _events.get(key)
    if existing:
        if existing.canonical_event_sha256 != event_digest:
            raise HTTPException(status_code=409, detail="event_id already exists for this tenant with different content")
        return existing
    stored = StoredEvent(event=event, payload_sha256=payload_digest, canonical_event_sha256=event_digest)
    _events[key] = stored
    return stored

@app.get("/v1/events", response_model=list[StoredEvent])
def list_events(
    tenant_id: str = Query(min_length=1, max_length=128),
    agent_id: str | None = None,
    run_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[StoredEvent]:
    results = [item for (tenant, _), item in _events.items() if tenant == tenant_id]
    if agent_id:
        results = [item for item in results if item.event.agent_id == agent_id]
    if run_id:
        results = [item for item in results if item.event.run_id == run_id]
    return sorted(results, key=lambda item: item.event.occurred_at)[:limit]

@app.get("/v1/evidence/verify")
def verify_evidence(content: str, expected_sha256: str = Query(min_length=64, max_length=64)) -> dict[str, Any]:
    """Development utility; production verification must operate on preserved original bytes."""
    valid = verify_digest(content.encode("utf-8"), expected_sha256)
    return {
        "valid": valid,
        "algorithm": "sha256",
        "scope": "exact UTF-8 bytes supplied to this endpoint",
        "limitation": "A matching digest does not prove source authenticity or collection completeness.",
    }

@app.get("/v1/meta")
def metadata() -> dict[str, Any]:
    return {
        "service": "ORACLE CONTROL",
        "api_version": app.version,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "storage": "volatile-development-memory",
        "production_ready": False,
    }
