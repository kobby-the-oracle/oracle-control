# API reference (initial version)

All protected endpoints require `X-API-Key`. The server maps each key to one tenant, subject and role list. Supported bootstrap roles include `admin`, `analyst`, `collector` and `auditor`; writes are role-gated. Do not use API keys as a substitute for production OIDC/SAML, SCIM and workload identity.

## Public
- `GET /health` — liveness response.
- `GET /docs` — interactive OpenAPI reference.

## Events
- `POST /v1/events` — ingest an event. Event tenant must match authenticated tenant. Same tenant/event ID and same content is idempotent; conflicting content returns 409.
- `GET /v1/events?agent_id=&run_id=&limit=` — tenant-scoped timeline slice.

## Investigations
- `POST /v1/cases` — create a case (title, description, severity).
- `GET /v1/cases` — list tenant cases.
- `GET /v1/cases/{case_id}` — case and findings.
- `POST /v1/cases/{case_id}/findings` — add a finding with explicit confidence and optional evidence IDs.
- `PATCH /v1/cases/{case_id}/status?status=` — change status with audit record.
- `GET /v1/cases/{case_id}/export` — export ZIP with case, linked event timeline, findings, evidence bytes, custody history and manifest; verifies evidence digests before inclusion.

## Evidence
- `POST /v1/evidence` — multipart upload; optional case_id, source_system and source_reference.
- `GET /v1/evidence?case_id=` — list tenant evidence metadata.
- `POST /v1/evidence/{evidence_id}/verify` — recompute SHA-256 against stored bytes.
- `GET /v1/evidence/{evidence_id}/download` — audited evidence download.

## Audit
- `GET /v1/audit?limit=` — tenant-scoped access and action records.

## Limitations
The current API is an engineering foundation. API-key auth is a bootstrap adapter; local filesystem evidence storage is not WORM/object-lock storage; SQLAlchemy create_all is not a production migration strategy; audit rows are not yet cryptographically chained; there is no production OIDC, SAML, SCIM, KMS, legal-hold engine or full case permissions model.

## Agent intelligence
- `POST /v1/agents` — register/update an agent identity.
- `GET /v1/agents` — inventory registered and observed agents.
- `GET /v1/agents/{agent_id}` — agent profile and recent activity.

## Authority intelligence
- `POST /v1/authority/records` — record a grant, denial, revocation or unknown authority state.
- `GET /v1/authority/records?agent_id=` — query authority history.
- `POST /v1/authority/approvals` — record human approval/denial.
- `GET /v1/authority/approvals?agent_id=` — query approval history.

## Risk and case briefing
- `GET /v1/intelligence/risk?agent_id=&limit=` — transparent heuristic triage indicators, not probability.
- `GET /v1/intelligence/cases/{case_id}/briefing` — evidence-context assembly for a human or future model adapter; does not produce an AI conclusion.

Cases may include `agent_ids` to scope authority context.

## AI investigation assistant
- `POST /v1/assistant/cases/{case_id}/draft` — assemble case evidence context; when an OpenAI-compatible model provider is explicitly enabled, request a structured analyst draft. Provider calls are disabled by default. Payloads are omitted unless `include_event_payloads=true`. Every returned evidence citation is checked against evidence attached to the case. Human review remains mandatory.

## Chain of custody
- `GET /v1/custody/evidence/{evidence_id}` — list hash-chained custody actions.
- `POST /v1/custody/evidence/{evidence_id}/transfer` — append a custody transfer record.
- `GET /v1/custody/evidence/{evidence_id}/verify` — recompute the evidence-specific custody hash chain.

Evidence collection, verification, download and case export append custody records. Hash chaining is tamper-evident against partial record edits, but a privileged database operator could rewrite the entire chain; external WORM storage or signed external anchoring remains necessary.

## Legal holds
- `POST /v1/legal-holds` — place an audited case-level or evidence-level hold.
- `GET /v1/legal-holds?case_id=` — list holds.
- `POST /v1/legal-holds/{hold_id}/release` — record authorised release.

The current legal-hold registry records lifecycle and audit metadata; it does not yet enforce storage retention or deletion locks at the object-storage layer.

## Source connector ingestion
- `POST /v1/connectors/aws/cloudtrail/events` — authenticated batch push of CloudTrail records; adapter normalises selected metadata and excludes request/response bodies.
- `POST /v1/connectors/opentelemetry/spans` — authenticated batch push of OpenTelemetry span JSON; adapter allowlists selected semantic attributes.
- `GET /v1/connectors/catalog` — available record adapters and planned source families.

These endpoints accept pushed records. They do not yet manage source credentials, poll APIs, maintain checkpoints or perform historical backfill.

## Cross-system forensic correlation
- `GET /v1/investigations/cases/{case_id}/timeline?limit=` — expands the case timeline through shared run/session identifiers, declared parent-run references and linked agents; evaluates available time-bounded authority records against event action/resource context. Every relationship includes its basis and confidence label. Correlation does not establish causation, and a matching authority record does not prove enforcement by the source system.

## Enterprise identity
- Send an OIDC access token as `Authorization: Bearer <token>`. The API validates the JWT signature against the configured JWKS, plus issuer, audience, expiry and required claims.
- Configure `ORACLE_OIDC_ISSUER`, `ORACLE_OIDC_AUDIENCE`, `ORACLE_OIDC_JWKS_URL`, `ORACLE_OIDC_TENANT_CLAIM` and `ORACLE_OIDC_ROLE_CLAIM`.
- The default tenant claim is `tenant_id`; `org_id` is accepted as a fallback. The default role claim is `roles`. Role names must map to ORACLE CONTROL roles such as `analyst`, `auditor`, `collector` and `admin`.
- The API does not implement the interactive login flow; use the organisation's OIDC identity provider and a trusted client application. API keys remain available for controlled service integrations.
- Production rollout still requires issuer-specific claim mapping, MFA policy at the identity provider, key rotation validation, negative tests, SCIM lifecycle provisioning and a documented break-glass process.

## Additional audit adapters
- `POST /v1/connectors/azure/activity-logs` — accepts Azure Activity Log record batches.
- `POST /v1/connectors/gcp/audit-logs` — accepts Google Cloud Audit Log record batches.
- `POST /v1/connectors/github/audit-logs` — accepts GitHub audit record batches with a stable source record ID.
These are authenticated push adapters. They do not yet provision source credentials, poll provider APIs, maintain durable cursors or backfill history.
