from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

Confidence = Literal["directly_observed", "correlated", "inferred", "unknown"]

class SourceMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    system: str = Field(min_length=1, max_length=256)
    event_id: str = Field(min_length=1, max_length=256)
    collector_id: str | None = None
    schema_version: str = "1.0"

class AgentEventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=1, max_length=256)
    tenant_id: str = Field(min_length=1, max_length=128)
    source: SourceMetadata
    event_type: str = Field(min_length=1, max_length=256)
    occurred_at: datetime
    agent_id: str | None = None
    run_id: str | None = None
    session_id: str | None = None
    parent_agent_id: str | None = None
    parent_run_id: str | None = None
    credential_ref: str | None = None
    actor_id: str | None = None
    resource_id: str | None = None
    relationship_confidence: Confidence = "directly_observed"
    payload: dict[str, Any]
    redaction_applied: bool = False

class StoredEvent(BaseModel):
    event: AgentEventIn
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload_sha256: str
    canonical_event_sha256: str
