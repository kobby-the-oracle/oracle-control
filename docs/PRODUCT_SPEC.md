# Product requirements

## Promise
Establish what AI agents did, under whose identity and authority, which tools/resources were affected, what evidence supports findings, and what remains unknown.

## Users
Incident responders, digital-forensics teams, security operations, AI platform owners, risk/compliance, internal audit and legal/privacy stakeholders.

## P0 — first commercial release foundation
- Agent, tenant, actor, run/session and source identity.
- Structured event ingestion with source and ingestion timestamps.
- Original payload preservation, provenance and deterministic digest.
- Normalised cross-system event timeline.
- Case and finding model with evidence references.
- Evidence integrity verification and export manifest.
- Authentication/authorisation integration points, audit events and tenant isolation.
- OpenTelemetry-compatible ingestion and documented connector contract.
- Cloud and customer-controlled deployment path using the same codebase.

## P1 — enterprise breadth
Identity providers, cloud audit logs, SaaS, databases, endpoint/security platforms, approvals, legal holds, retention, customer-managed keys, SIEM/SOAR and ticketing integrations.

## P2 — advanced intelligence
Behaviour baselines, explainable anomaly detection, evidence completeness scoring, blast-radius reconstruction, evidence-citing investigation assistant and human-approved response recommendations.

## Acceptance criteria
- Ingested event retains source ID, source timestamp, ingestion timestamp and original payload.
- Same tenant/source/event replay is idempotent; conflicting replay is rejected.
- Original digest can be independently recomputed.
- Timeline distinguishes source time from ingestion time.
- Integrity verification detects modified evidence.
- Every finding cites evidence or explicitly records its absence.
- Cross-tenant access is rejected.
- Export contains manifest, digests, provenance and collection limitations.

## Non-goals
Not a SIEM replacement, agent framework or generic observability dashboard. The platform cannot reconstruct events that source systems never recorded.
