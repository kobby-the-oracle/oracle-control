from datetime import datetime, timezone
from typing import Any
from oracle_control.models import AgentEventIn

SAFE_ATTRIBUTES = {
    "gen_ai.system","gen_ai.operation.name","gen_ai.request.model","gen_ai.response.model",
    "gen_ai.agent.name","gen_ai.tool.name","server.address","http.request.method",
    "http.response.status_code","db.system","db.operation.name","service.name",
    "enduser.id","oracle.agent.id","oracle.run.id","oracle.resource.id",
}

class OpenTelemetrySpanAdapter:
    name = "opentelemetry"
    def parse(self, span: dict[str, Any], *, tenant_id: str) -> AgentEventIn:
        context=span.get("spanContext") or span.get("context") or {}
        span_id=context.get("spanId") or span.get("spanId")
        trace_id=context.get("traceId") or span.get("traceId")
        if not span_id or not trace_id: raise ValueError("OpenTelemetry traceId and spanId are required")
        start=span.get("startTimeUnixNano") or span.get("start_time_unix_nano")
        if not start: raise ValueError("OpenTelemetry start timestamp is required")
        occurred=datetime.fromtimestamp(int(start)/1_000_000_000,tz=timezone.utc)
        raw_attrs=span.get("attributes") or {}
        if isinstance(raw_attrs,list):
            attrs={item.get("key"):item.get("value",{}).get("stringValue") for item in raw_attrs if item.get("key")}
        else: attrs=raw_attrs
        safe={k:v for k,v in attrs.items() if k in SAFE_ATTRIBUTES}
        return AgentEventIn(
            event_id=f"otel:{trace_id}:{span_id}",tenant_id=tenant_id,
            source={"system":self.name,"event_id":str(span_id),"schema_version":"1.0"},
            event_type=str(span.get("name") or "otel.span"),
            occurred_at=occurred,agent_id=safe.get("oracle.agent.id") or safe.get("gen_ai.agent.name"),
            run_id=safe.get("oracle.run.id") or str(trace_id),
            actor_id=safe.get("enduser.id"),resource_id=safe.get("oracle.resource.id"),
            relationship_confidence="directly_observed",payload={"trace_id":trace_id,"span_id":span_id,"attributes":safe},
            redaction_applied=True,
        )
