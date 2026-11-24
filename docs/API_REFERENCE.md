# API reference (initial version)

All protected endpoints require `X-API-Key`. The key is mapped server-side to exactly one tenant using `ORACLE_API_KEYS`. Do not use this bootstrap mechanism as a substitute for production OIDC/SAML and workload identity.

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
- `GET /v1/cases/{case_id}/export` — export ZIP with case, findings, evidence bytes and manifest; verifies evidence digests before inclusion.

## Evidence
- `POST /v1/evidence` — multipart upload; optional case_id, source_system and source_reference.
- `GET /v1/evidence?case_id=` — list tenant evidence metadata.
- `POST /v1/evidence/{evidence_id}/verify` — recompute SHA-256 against stored bytes.
- `GET /v1/evidence/{evidence_id}/download` — audited evidence download.

## Audit
- `GET /v1/audit?limit=` — tenant-scoped access and action records.

## Limitations
The current API is an engineering foundation. API-key auth is a bootstrap adapter; local filesystem evidence storage is not WORM/object-lock storage; SQLAlchemy create_all is not a production migration strategy; audit rows are not yet cryptographically chained; there is no production OIDC, SAML, SCIM, KMS, legal-hold engine or full case permissions model.
