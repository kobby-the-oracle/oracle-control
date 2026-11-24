from datetime import datetime, timezone
from typing import Any

from oracle_control.models import AgentEventIn


def _parse_time(value: Any) -> datetime:
    if not value:
        raise ValueError("Source event timestamp is required")
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class AzureActivityLogAdapter:
    name = "azure-activity-logs"

    def parse(self, record: dict[str, Any], *, tenant_id: str) -> AgentEventIn:
        event_id = str(record.get("eventDataId") or record.get("id") or "")
        if not event_id:
            raise ValueError("Azure activity eventDataId/id is required")
        operation = record.get("operationName") or {}
        if isinstance(operation, dict):
            operation = operation.get("value") or operation.get("localizedValue")
        status = record.get("status") or {}
        if isinstance(status, dict):
            status = status.get("value") or status.get("localizedValue")
        # Do not persist Azure claims, authorization headers or request/response bodies.
        safe_payload = {
            "operation": operation,
            "category": (record.get("category") or {}).get("value") if isinstance(record.get("category"), dict) else record.get("category"),
            "result": status,
            "level": record.get("level"),
            "resource_provider": record.get("resourceProviderName", {}).get("value") if isinstance(record.get("resourceProviderName"), dict) else record.get("resourceProviderName"),
            "correlation_id": record.get("correlationId"),
            "caller_ip": record.get("callerIpAddress"),
        }
        safe_payload = {key: value for key, value in safe_payload.items() if value is not None}
        return AgentEventIn(
            event_id=f"azure:{event_id}", tenant_id=tenant_id,
            source={"system": self.name, "event_id": event_id, "schema_version": "1.0"},
            event_type=f"azure.activity.{str(operation or 'unknown')}",
            occurred_at=_parse_time(record.get("eventTimestamp") or record.get("time")),
            actor_id=record.get("caller"),
            resource_id=record.get("resourceId"),
            relationship_confidence="directly_observed",
            payload=safe_payload, redaction_applied=True,
        )


class GoogleCloudAuditLogAdapter:
    name = "google-cloud-audit-logs"

    def parse(self, record: dict[str, Any], *, tenant_id: str) -> AgentEventIn:
        event_id = str(record.get("insertId") or record.get("insert_id") or "")
        if not event_id:
            raise ValueError("Google audit log insertId is required")
        proto = record.get("protoPayload") or {}
        authentication = proto.get("authenticationInfo") or {}
        request = proto.get("requestMetadata") or {}
        resource = record.get("resource") or {}
        labels = resource.get("labels") or {}
        safe_payload = {
            "method_name": proto.get("methodName"),
            "service_name": proto.get("serviceName"),
            "status_code": (proto.get("status") or {}).get("code"),
            "caller_ip": request.get("callerIp"),
            "resource_type": resource.get("type"),
            "project_id": labels.get("project_id"),
        }
        safe_payload = {key: value for key, value in safe_payload.items() if value is not None}
        return AgentEventIn(
            event_id=f"gcp-audit:{event_id}", tenant_id=tenant_id,
            source={"system": self.name, "event_id": event_id, "schema_version": "1.0"},
            event_type=f"gcp.audit.{proto.get('methodName') or 'unknown'}",
            occurred_at=_parse_time(record.get("timestamp")),
            actor_id=authentication.get("principalEmail"),
            resource_id=proto.get("resourceName"),
            relationship_confidence="directly_observed",
            payload=safe_payload, redaction_applied=True,
        )


class GitHubAuditLogAdapter:
    name = "github-audit-log"

    def parse(self, record: dict[str, Any], *, tenant_id: str) -> AgentEventIn:
        event_id = str(record.get("_document_id") or record.get("audit_log_id") or record.get("id") or "")
        if not event_id:
            # Some GitHub audit exports omit a stable document ID. Refuse to invent one.
            raise ValueError("GitHub audit record requires a stable _document_id/audit_log_id/id")
        action = record.get("action") or "unknown"
        actor = record.get("actor") or record.get("user")
        repository = record.get("repo") or record.get("repository")
        org = record.get("org") or record.get("organization")
        safe_payload = {
            "action": action,
            "actor": actor,
            "actor_id": record.get("actor_id"),
            "repository": repository,
            "organization": org,
            "operation_type": record.get("operation_type"),
            "transport_protocol": record.get("transport_protocol"),
            "programmatic_access_type": record.get("programmatic_access_type"),
            "hashed_token": record.get("hashed_token"),
        }
        safe_payload = {key: value for key, value in safe_payload.items() if value is not None}
        return AgentEventIn(
            event_id=f"github-audit:{event_id}", tenant_id=tenant_id,
            source={"system": self.name, "event_id": event_id, "schema_version": "1.0"},
            event_type=f"github.audit.{action}",
            occurred_at=_parse_time(record.get("@timestamp") or record.get("created_at")),
            actor_id=str(actor) if actor is not None else None,
            resource_id=str(repository or org) if repository or org else None,
            relationship_confidence="directly_observed",
            payload=safe_payload, redaction_applied=True,
        )
