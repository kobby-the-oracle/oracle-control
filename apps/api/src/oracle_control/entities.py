from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from oracle_control.db import Base

def utcnow():
    return datetime.now(timezone.utc)

class EventRecord(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("tenant_id", "event_id", name="uq_event_tenant_event"), Index("ix_event_tenant_time", "tenant_id", "occurred_at"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    event_id: Mapped[str] = mapped_column(String(256))
    source_system: Mapped[str] = mapped_column(String(256))
    source_event_id: Mapped[str] = mapped_column(String(256))
    event_type: Mapped[str] = mapped_column(String(256))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    agent_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    confidence: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON)
    payload_sha256: Mapped[str] = mapped_column(String(64))
    event_sha256: Mapped[str] = mapped_column(String(64))
    redaction_applied: Mapped[bool] = mapped_column(default=False)

class CaseRecord(Base):
    __tablename__ = "cases"
    __table_args__ = (Index("ix_case_tenant_status", "tenant_id", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    status: Mapped[str] = mapped_column(String(24), default="open")
    created_by: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    findings: Mapped[list["FindingRecord"]] = relationship(back_populates="case", cascade="all, delete-orphan")

class FindingRecord(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(300))
    statement: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(32))
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case: Mapped["CaseRecord"] = relationship(back_populates="findings")

class EvidenceRecord(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.id"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(512))
    media_type: Mapped[str] = mapped_column(String(256))
    storage_path: Mapped[str] = mapped_column(Text)
    byte_length: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    source_system: Mapped[str] = mapped_column(String(256), default="analyst-upload")
    source_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    collected_by: Mapped[str] = mapped_column(String(256))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

class AuditRecord(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), index=True)
    actor: Mapped[str] = mapped_column(String(256))
    action: Mapped[str] = mapped_column(String(128))
    object_type: Mapped[str] = mapped_column(String(64))
    object_id: Mapped[str] = mapped_column(String(256))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
