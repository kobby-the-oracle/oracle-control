from oracle_control.connectors.cloudtrail import CloudTrailConnector
from oracle_control.connectors.otel import OpenTelemetrySpanAdapter

def test_cloudtrail_adapter_preserves_source_provenance_and_omits_request_body():
    event=CloudTrailConnector().parse({
        "eventID":"id-123","eventTime":"2026-11-24T01:00:00Z","eventSource":"s3.amazonaws.com",
        "eventName":"GetObject","awsRegion":"eu-west-1","requestParameters":{"secret":"do-not-copy"},
        "userIdentity":{"arn":"arn:aws:sts::123:assumed-role/agent/session"},
        "resources":[{"ARN":"arn:aws:s3:::private-bucket/key"}]
    },tenant_id="tenant-a")
    assert event.source.event_id=="id-123"
    assert event.resource_id=="arn:aws:s3:::private-bucket/key"
    assert "requestParameters" not in event.payload

def test_otel_adapter_allowlists_attributes_and_links_trace():
    event=OpenTelemetrySpanAdapter().parse({
        "spanContext":{"traceId":"trace-1","spanId":"span-1"},
        "name":"tool.invoke","startTimeUnixNano":"1795482000000000000",
        "attributes":{"gen_ai.tool.name":"search","prompt":"private prompt","oracle.agent.id":"agent-1"}
    },tenant_id="tenant-a")
    assert event.run_id=="trace-1"
    assert event.agent_id=="agent-1"
    assert "prompt" not in event.payload["attributes"]
