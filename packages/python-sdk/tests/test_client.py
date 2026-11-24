import httpx
from oracle_control_sdk.client import OracleControlClient

def test_emit_adds_tenant_and_auth_header():
    seen = {}
    def handler(request):
        seen["body"] = request.read()
        seen["auth"] = request.headers["X-API-Key"]
        return httpx.Response(201, json={"ok": True})
    client = OracleControlClient("https://oracle.example", "secret", "tenant-a")
    client._client.close()
    client._client = httpx.Client(base_url="https://oracle.example",
        headers={"X-API-Key":"secret"},transport=httpx.MockTransport(handler))
    result = client.emit({"event_id":"e1","source":{"system":"test","event_id":"s1"},
        "event_type":"test","occurred_at":"2026-11-24T00:00:00Z","payload":{}})
    assert result["ok"] is True
    assert b'"tenant_id":"tenant-a"' in seen["body"]
    assert seen["auth"]=="secret"
    client.close()
