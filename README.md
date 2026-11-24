# ORACLE CONTROL

**Evidence-centred AI incident investigation and digital forensics.**

ORACLE CONTROL is being built to establish what AI agents did, under whose identity and authority, which tools and resources were affected, what evidence supports each conclusion, and where the record is incomplete.

> Forensic integrity rule: SHA-256 establishes whether collected bytes changed after hashing. It does not prove source authenticity, source truthfulness, collection completeness or legal admissibility.

## Repository map
- `apps/api` — FastAPI, PostgreSQL persistence, tenant-scoped event/case/evidence/authority APIs.
- `apps/web` — React console connected to the API.
- `packages/schemas` — versioned agent event contract.
- `packages/python-sdk` and `packages/typescript-sdk` — first-party agent telemetry SDKs.
- `docs` — requirements, architecture, security, API and integration specifications.
- `infra` — Docker Compose for local API, PostgreSQL and web console.
- `.github/workflows` — CI checks.

## Implemented engineering foundations
- Structured event ingestion with source provenance and idempotent replay.
- PostgreSQL persistence models for events, agents, cases, findings, evidence, approvals, authority and audit records.
- Tenant-scoped API-key bootstrap authentication.
- Agent inventory and activity timeline.
- Case creation, findings, status transitions and agent linking.
- Evidence upload, SHA-256 digest, integrity verification, audited download and verified ZIP case export.
- Authority and human approval record APIs.
- Explainable rule-based risk triage.
- Optional OpenAI-compatible investigation draft adapter; disabled by default and validates evidence citations.
- OpenTelemetry span and AWS CloudTrail record mapping adapters and authenticated batch ingest endpoints.
- First-party Python and TypeScript SDKs for agent event emission.
- React console with API connection, live tenant data, case creation, evidence upload and authority/risk/assistant views.
- Docker Compose, Alembic baseline, GitHub Actions CI, and a private Supabase Storage adapter for evidence objects (requires a private bucket and server-only credentials).
- Supabase PostgreSQL schema provisioned for the ORACLE CONTROL project; the API still requires a deployment host with its database connection secret configured before it uses the managed database.

## Run locally with Docker
Requires Docker Compose.

1. Copy `.env.example` to `.env`.
2. Replace the example API key with a long random secret.
3. Start from the repository root:

```bash
docker compose --env-file .env -f infra/docker-compose.yml up --build
```

- Web console: http://localhost:8080
- API: http://localhost:8000
- OpenAPI docs: http://localhost:8000/docs

Enter the API URL and the matching tenant API key in the console. The API key is held in browser memory only.

## Run the API without Docker
Python 3.11+:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
export ORACLE_API_KEYS='{"replace-with-a-long-random-key":{"tenant_id":"demo-tenant","subject":"local-admin","roles":["admin","analyst","collector","auditor"]}}'
uvicorn oracle_control.main:app --reload
```

Run tests:

```bash
cd apps/api
pytest -q
ruff check src tests
```

## Honest release status
This is a working engineering foundation, **not yet a production-ready enterprise release**. API-key auth is a bootstrap mechanism, evidence is stored on a local filesystem volume (not WORM/object-lock), the audit log is not cryptographically chained, and OIDC/SAML/SCIM, customer-managed KMS, legal holds, full role-based case permissions, production connector workers, high availability and air-gapped update/licensing remain unfinished. OpenTelemetry and CloudTrail code currently maps individual records; it does not yet establish live source connections or reliable backfill/checkpoint operations. AI model calls require explicit provider configuration and are off by default.

See [security policy](SECURITY.md), [contribution guide](CONTRIBUTING.md), [data governance](docs/DATA_GOVERNANCE.md), [operations runbook](docs/OPERATIONS.md), the [SDK guide](docs/SDK_GUIDE.md), [Product module status](docs/PRODUCT_MODULES.md), [deployment guide](docs/DEPLOYMENT.md), [product requirements](docs/PRODUCT_SPEC.md), [architecture](docs/ARCHITECTURE.md), [security model](docs/SECURITY_MODEL.md), [threat model](docs/THREAT_MODEL.md), [differentiation](docs/DIFFERENTIATION.md), [competitive landscape](docs/COMPETITIVE_LANDSCAPE.md), [validation plan](docs/VALIDATION_PLAN.md), [API reference](docs/API_REFERENCE.md) and [integration programme](docs/INTEGRATIONS.md).
