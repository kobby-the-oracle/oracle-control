from collections import defaultdict
from datetime import timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from oracle_control.db import get_db
from oracle_control.entities import AuthorityRecord, CaseRecord, EventRecord
from oracle_control.security import require_roles

router = APIRouter(prefix="/v1/investigations", tags=["forensic correlation"])


def _utc(value):
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _scope_matches(scope: str, resource: str | None) -> bool:
    if not resource:
        return False
    if scope.endswith("*"):
        return resource.startswith(scope[:-1])
    return resource == scope or resource.startswith(scope.rstrip("/") + "/")


def _authority_context(db: Session, tenant: str, event: EventRecord) -> dict[str, Any]:
    if not event.agent_id:
        return {"status": "insufficient_event_context", "records": []}
    records = db.query(AuthorityRecord).filter_by(
        tenant_id=tenant, agent_id=event.agent_id
    ).all()
    action = str((event.payload or {}).get("tool") or event.event_type)
    occurred = _utc(event.occurred_at)
    candidates = []
    for record in records:
        start, end = _utc(record.valid_from), _utc(record.valid_until)
        temporal = bool(start and occurred and start <= occurred and (end is None or occurred <= end))
        permission_match = record.permission in {"*", action} or action.endswith(record.permission)
        resource_match = _scope_matches(record.resource_scope, event.resource_id)
        if temporal and permission_match and resource_match:
            match = "matching_grant" if record.decision == "granted" else "matching_deny" if record.decision == "denied" else "matching_record"
        elif not temporal:
            match = "outside_validity_window"
        elif not event.resource_id:
            match = "resource_context_missing"
        else:
            match = "scope_or_permission_mismatch"
        candidates.append({
            "authority_record_id": record.id,
            "principal_id": record.principal_id,
            "permission": record.permission,
            "resource_scope": record.resource_scope,
            "decision": record.decision,
            "source_system": record.source_system,
            "valid_from": record.valid_from,
            "valid_until": record.valid_until,
            "match": match,
            "evidence_ids": record.evidence_ids,
        })
    matching = [item for item in candidates if item["match"] in {"matching_grant", "matching_deny", "matching_record"}]
    status = "matching_authority_record" if matching else "no_matching_authority_record"
    return {
        "status": status,
        "action_compared": action,
        "resource_compared": event.resource_id,
        "records": candidates,
        "limitation": "A matching authority record is contextual evidence, not proof that the source system enforced the permission or that the action was authorised.",
    }


@router.get("/cases/{case_id}/timeline")
def investigation_timeline(
    case_id: str,
    limit: int = Query(default=1000, ge=1, le=5000),
    principal=Depends(require_roles("analyst", "auditor", "admin")),
    db: Session = Depends(get_db),
):
    tenant = principal["tenant_id"]
    case = db.query(CaseRecord).filter_by(id=case_id, tenant_id=tenant).first()
    if not case:
        raise HTTPException(404, "Case not found")

    seed_agents = set(case.agent_ids or [])
    seed_query = db.query(EventRecord).filter(EventRecord.tenant_id == tenant)
    if seed_agents:
        seed_query = seed_query.filter(EventRecord.agent_id.in_(seed_agents))
    else:
        seed_query = seed_query.filter(EventRecord.id == -1)
    seed_events = seed_query.order_by(EventRecord.occurred_at.asc()).limit(limit).all()

    run_ids = {row.run_id for row in seed_events if row.run_id}
    session_ids = {row.session_id for row in seed_events if row.session_id}
    parent_run_ids = {row.parent_run_id for row in seed_events if row.parent_run_id}
    related_agents = seed_agents | {row.parent_agent_id for row in seed_events if row.parent_agent_id}
    related_query = db.query(EventRecord).filter(EventRecord.tenant_id == tenant)
    predicates = []
    if run_ids:
        predicates.append(EventRecord.run_id.in_(run_ids))
    if session_ids:
        predicates.append(EventRecord.session_id.in_(session_ids))
    if parent_run_ids:
        predicates.append(EventRecord.run_id.in_(parent_run_ids))
    if related_agents:
        predicates.append(EventRecord.agent_id.in_(related_agents))
    if not predicates:
        rows = seed_events
    else:
        related_rows = related_query.filter(or_(*predicates)).order_by(EventRecord.occurred_at.asc()).limit(limit).all()
        by_id = {row.id: row for row in [*seed_events, *related_rows]}
        rows = sorted(by_id.values(), key=lambda row: (_utc(row.occurred_at), row.id))[:limit]

    edges: dict[tuple[str, str, str], dict[str, str]] = {}
    groups: dict[tuple[str, str], list[EventRecord]] = defaultdict(list)
    for row in rows:
        if row.run_id:
            groups[("run", row.run_id)].append(row)
        if row.session_id:
            groups[("session", row.session_id)].append(row)
    for (kind, value), group in groups.items():
        ordered = sorted(group, key=lambda row: (_utc(row.occurred_at), row.id))
        for previous, current in zip(ordered, ordered[1:]):
            if previous.id != current.id:
                key = (previous.event_id, current.event_id, kind)
                edges[key] = {
                    "from_event_id": previous.event_id,
                    "to_event_id": current.event_id,
                    "relationship": f"shared_{kind}",
                    "confidence": "correlated",
                    "basis": f"Both records contain the same {kind}_id",
                }
    event_by_run = {row.run_id: row for row in rows if row.run_id}
    for row in rows:
        parent = event_by_run.get(row.parent_run_id) if row.parent_run_id else None
        if parent and parent.id != row.id:
            key = (parent.event_id, row.event_id, "parent_run")
            edges[key] = {
                "from_event_id": parent.event_id,
                "to_event_id": row.event_id,
                "relationship": "declared_parent_run",
                "confidence": "directly_observed",
                "basis": "Child event explicitly references parent_run_id",
            }

    event_items = []
    for row in rows:
        event_items.append({
            "event_id": row.event_id,
            "source_system": row.source_system,
            "source_event_id": row.source_event_id,
            "event_type": row.event_type,
            "occurred_at": row.occurred_at,
            "ingested_at": row.ingested_at,
            "agent_id": row.agent_id,
            "run_id": row.run_id,
            "session_id": row.session_id,
            "parent_agent_id": row.parent_agent_id,
            "parent_run_id": row.parent_run_id,
            "actor_id": row.actor_id,
            "credential_ref": row.credential_ref,
            "resource_id": row.resource_id,
            "relationship_confidence": row.confidence,
            "payload_sha256": row.payload_sha256,
            "case_agent_match": row.agent_id in seed_agents,
            "authority_context": _authority_context(db, tenant, row),
        })

    return {
        "case_id": case.id,
        "events": event_items,
        "relationships": list(edges.values()),
        "event_count": len(event_items),
        "relationship_count": len(edges),
        "relationship_semantics": {
            "directly_observed": "An explicit source identifier or record establishes the relationship.",
            "correlated": "Records share identifiers or context; this does not prove causation.",
            "inferred": "An analytical hypothesis requiring analyst review.",
            "unknown": "The relationship cannot be established from available records.",
        },
        "collection_limitations": [
            "Only ingested records available to this tenant are considered.",
            "The timeline expands through shared run, session and parent-run identifiers; it is not proof that every related event has been collected.",
            "A matching authority record does not prove that the source system enforced it.",
            "Timestamp ordering does not establish causation; source clock uncertainty may affect ordering.",
        ],
    }
