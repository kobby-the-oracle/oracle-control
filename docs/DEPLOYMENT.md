# Deployment guide

## Local development
Copy `.env.example` to `.env`, set a long random `ORACLE_API_KEYS` value, then run:

```bash
docker compose --env-file .env -f infra/docker-compose.yml up --build
```

Console: http://localhost:8080. API: http://localhost:8000. OpenAPI: http://localhost:8000/docs.

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
