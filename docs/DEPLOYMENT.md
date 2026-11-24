# Deployment guide

## Local development
Copy `.env.example` to `.env`, set a long random `ORACLE_API_KEYS` value, then run:

```bash
docker compose --env-file .env -f infra/docker-compose.yml up --build
```

Console: http://localhost:8080. API: http://localhost:8000. OpenAPI: http://localhost:8000/docs.

## Supabase managed database and evidence storage

The API can use Supabase Postgres through SQLAlchemy and a private Supabase Storage bucket for evidence. Use the project's **Connect** dialog to copy a direct Postgres connection string for a long-lived IPv6-capable backend, or the **session pooler** string for a persistent backend on an IPv4-only network. Add `sslmode=require` and set it as `ORACLE_DATABASE_URL` in the backend host's secret manager. Never commit the database password or the Supabase service-role/secret key.

The private Storage bucket `oracle-control-evidence` is provisioned by the Supabase migration in this repository (25 MiB per object). Confirm it remains private. Configure the backend environment with `ORACLE_STORAGE_BACKEND=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_EVIDENCE_BUCKET=oracle-control-evidence`. The privileged key must remain server-side; the API enforces tenant-scoped access before reading or writing evidence.

The current adapter uploads with overwrite disabled and verifies SHA-256 on reads/exports. Supabase Storage does not provide object-lock/WORM guarantees; use a separate immutable archive or signed external anchoring for evidentiary retention requirements. The bucket must remain private.

For managed deployments set `ORACLE_AUTO_CREATE_SCHEMA=false`; schema changes must be applied by Alembic before the API starts. Local SQLite development auto-creates tables. Local Docker Compose explicitly enables schema creation.

## Database migrations
The API includes an Alembic baseline. From `apps/api` with the package installed and `ORACLE_DATABASE_URL` configured:

```bash
alembic upgrade head
```

The current app also calls SQLAlchemy `create_all` at startup for the development scaffold. Production release engineering must make migrations an explicit deployment step and remove schema creation from application startup.

## Cloud and customer-controlled deployment
The same application code is intended for managed cloud and customer-controlled infrastructure. This repository currently provides local Compose assets only. Before production deployment, add:
- Kubernetes/Helm charts, resource requests/limits and network policies.
- Managed PostgreSQL or supported customer database operations.
- S3-compatible object storage with versioning and object lock/WORM where required.
- Customer-controlled encryption keys and rotation.
- OIDC/SAML identity, SCIM provisioning and granular tenant/case authorisation.
- External secret manager integration; never place production API keys in source or images.
- TLS termination, ingress controls, egress policy and rate limits.
- Metrics, logs, traces, alerting and SLOs.
- Backup/restore drills, disaster recovery, upgrade and rollback procedures.

## Private and air-gapped mode
Do not claim air-gap support from this Compose setup. A true air-gapped distribution requires offline image and dependency bundles, offline licence activation, signed updates, local model option, no mandatory external control plane, and a documented support/update process.
