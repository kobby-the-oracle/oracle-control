# Product module status

This document separates implemented code from product capabilities that are still planned. A route or data model is not equivalent to a production-grade enterprise module.

| Product module | Present in repository | Remaining work before enterprise release |
|---|---|---|
| Agent intelligence | Agent registration, inventory from observed events, recent activity profiles | Framework-native identity, agent lifecycle, parent/child graph, runtime inventory sync |
| Evidence collection | Authenticated multipart upload, size limit, source metadata, digest | Native collectors, source authentication, cursor/backfill, collection health and gap detection |
| Authority intelligence | Manual authority grants/denials/revocations and approval records | Historical IAM/approval connectors, effective-permission evaluation and temporal graph |
| Forensic investigation | Cases, findings, status, agent links, event timeline API, case export | Cross-system graph correlation, custody workflows, collaborative review and case-level policy |
| Evidence vault | Local persistent bytes, SHA-256 verify, audited download, verified export | Object lock/WORM, customer-managed keys, retention, legal hold, signed manifests, custody signatures |
| AI investigation assistant | Optional OpenAI-compatible provider adapter; structured output; citation validation; disabled by default | Provider-specific controls, private model packaging, prompt-injection hardening, evaluation suite, review UX |
| Risk intelligence | Transparent heuristic scoring with reason codes | Baselines, calibrated detection, explainability evaluation, false-positive measurement and blast-radius models |
| Enterprise security | Tenant-scoped API-key mapping, tenant filters, audit records, CORS allowlist | OIDC/SAML, SCIM, RBAC/ABAC, MFA integration, KMS, secrets rotation, chained audit and penetration tests |
| Deployment infrastructure | API and web containers, PostgreSQL Compose, Alembic baseline | Helm/Kubernetes, HA, backup/restore, observability, offline install/update and support lifecycle |
| Enterprise integrations | CloudTrail and OpenTelemetry record mappers | Live connector services, credentials, checkpointing, retries, 15+ validated source integrations |

## Release gate
Do not call a module production-ready until it has:
1. Automated unit and integration tests.
2. Tenant isolation and failure-mode tests.
3. Security and privacy review.
4. Operational runbook and observability.
5. Upgrade, rollback and recovery plan.
6. Documented limits and customer acceptance criteria.
