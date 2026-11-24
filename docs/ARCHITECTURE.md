# Technical architecture

## Data flow
Agent frameworks and source systems -> OpenTelemetry/native collectors -> authenticated ingestion -> schema validation and normalisation -> raw evidence preservation -> event index/correlation -> case timeline/findings -> verified export.

## Initial stack
- API: Python 3.11+, FastAPI, Pydantic.
- UI: React and TypeScript.
- Event conventions: versioned JSON schema and OpenTelemetry GenAI semantic conventions where applicable.
- Target persistence: PostgreSQL for tenants, cases, event metadata and audit; S3-compatible object storage for original evidence.
- Analytics: start with PostgreSQL; add ClickHouse only when measured volume requires it.
- Search: indexed PostgreSQL initially; OpenSearch when justified.
- Identity: OIDC/SAML, short-lived service credentials, role/attribute-based access.
- Deployment: containers first; Helm/Kubernetes and offline/private profiles as hardening milestones.

## Event envelope
Tenant ID, source system and event ID, event type, schema version, source timestamp, ingestion timestamp, agent/run/session/parent-agent/parent-run/actor/resource references, opaque credential references, payload and collection metadata. Keep original source bytes separate from normalised fields. Record clock uncertainty.

## Correlation confidence
- directly_observed: explicit source record or identifier establishes the link.
- correlated: common IDs/time/resource context support a link but do not prove causation.
- inferred: analytical hypothesis requiring review.
- unknown: not established by available evidence.

## Trust-separated data
1. Raw evidence and provenance.
2. Normalised queryable events.
3. Derived correlations and AI analysis, clearly labelled.
4. Case records, analyst decisions and custody actions.

## Scaling
Begin as a modular monolith. Add durable queues and independently scaled workers when throughput, replay or backpressure requirements justify them. Avoid premature microservices. Ingestion must be idempotent.

## Deployment modes
Managed cloud and customer-controlled deployment use the same versioned components. Private deployment must document outbound dependencies and support customer-controlled keys. Air-gapped operation requires an offline licensing, update and support design; it is not assumed by this scaffold.
