from typing import Any
import httpx

class OracleControlClient:
    """Small push SDK. Caller supplies a stable event_id so retries remain idempotent."""
    def __init__(self, base_url: str, api_key: str, tenant_id: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            timeout=timeout,
        )

    def emit(self, event: dict[str, Any]) -> dict[str, Any]:
        body = dict(event)
        body["tenant_id"] = self.tenant_id
        response = self._client.post("/v1/events", json=body)
        response.raise_for_status()
        return response.json()

    def emit_tool_invocation(
        self, *, event_id: str, source_event_id: str, occurred_at: str,
        agent_id: str, run_id: str, tool_name: str, resource_id: str | None = None,
        actor_id: str | None = None, outcome: str = "unknown", session_id: str | None = None,
        parent_agent_id: str | None = None, parent_run_id: str | None = None,
        credential_ref: str | None = None,
    ) -> dict[str, Any]:
        return self.emit({
            "event_id": event_id,
            "source": {"system": "oracle-control-python-sdk", "event_id": source_event_id},
            "event_type": "tool.invoked",
            "occurred_at": occurred_at,
            "agent_id": agent_id,
            "run_id": run_id,
            "session_id": session_id,
            "parent_agent_id": parent_agent_id,
            "parent_run_id": parent_run_id,
            "credential_ref": credential_ref,
            "actor_id": actor_id,
            "resource_id": resource_id,
            "relationship_confidence": "directly_observed",
            "payload": {"tool_name": tool_name, "outcome": outcome},
            "redaction_applied": False,
        })

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
