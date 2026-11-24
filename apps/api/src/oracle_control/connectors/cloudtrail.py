from datetime import datetime, timezone
from typing import Any
from oracle_control.models import AgentEventIn

class CloudTrailConnector:
    name = "aws-cloudtrail"
    def parse(self, record: dict[str, Any], *, tenant_id: str) -> AgentEventIn:
        event_id = str(record.get("eventID") or "")
        if not event_id: raise ValueError("CloudTrail eventID is required")
        occurred = record.get("eventTime")
        if not occurred: raise ValueError("CloudTrail eventTime is required")
        identity = record.get("userIdentity") or {}
        resources = record.get("resources") or []
        resource_id = None
        if resources:
            first=resources[0] or {}
            resource_id=first.get("ARN") or first.get("arn")
        # Deliberately avoid copying request/response bodies and credentials into the event.
        safe_payload = {
            "event_source": record.get("eventSource"),
            "event_name": record.get("eventName"),
            "aws_region": record.get("awsRegion"),
            "source_ip": record.get("sourceIPAddress"),
            "user_agent": record.get("userAgent"),
            "error_code": record.get("errorCode"),
            "read_only": record.get("readOnly"),
        }
        safe_payload = {k:v for k,v in safe_payload.items() if v is not None}
        return AgentEventIn(
            event_id=f"cloudtrail:{event_id}", tenant_id=tenant_id,
            source={"system":self.name,"event_id":event_id,"schema_version":"1.0"},
            event_type=f"cloudtrail.{record.get('eventName') or 'unknown'}",
            occurred_at=datetime.fromisoformat(str(occurred).replace("Z","+00:00")),
            agent_id=identity.get("sessionContext",{}).get("sessionIssuer",{}).get("userName"),
            actor_id=identity.get("arn") or identity.get("principalId"),
            resource_id=resource_id, relationship_confidence="directly_observed",
            payload=safe_payload, redaction_applied=True,
        )
