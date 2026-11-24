# Security and forensic integrity

## Required production controls
- OIDC/SAML authentication and MFA via identity provider.
- Tenant-scoped authorisation on every read and write.
- TLS in transit and encryption at rest; customer-managed keys.
- Secrets manager, rotation and no credentials in logs or payloads.
- Least-privilege collector credentials, health monitoring and revocation.
- Append-only audit trail for evidence access, export, verification and case changes.
- WORM/immutable object retention where required.
- Rate limits, payload limits, schema validation and upload scanning.
- Redaction before broad indexing; explicit sensitive-data access policy.
- Tested backups, restore, vulnerability management and incident response.

## Forensic rules
- Hash original bytes at accepted collection.
- Record algorithm, digest, byte length, source and collector identity, timestamps and custody actions.
- Verify digest on retrieval/export.
- Keep source and ingestion timestamps distinct.
- Record partial, failed and unavailable collection attempts.
- A matching digest establishes post-hash integrity only—not authenticity, truthfulness, completeness or legal admissibility.
- Label relationships directly_observed, correlated, inferred or unknown.
- AI-generated analysis is a lead, not evidence; cite source records and require human review.

## Privacy
Do not collect model chain-of-thought. Collect operational metadata and only necessary inputs/outputs where lawful. Support redaction, retention and deletion policies by tenant and jurisdiction.

## Current API access roles
The bootstrap API-key adapter supports tenant-scoped `admin`, `analyst`, `collector` and `auditor` roles. Write endpoints are role-gated. This is basic RBAC only; OIDC/SAML identity federation, SCIM lifecycle, attribute-based case permissions and policy administration remain production requirements.

## Evidence custody and legal holds
Evidence collection, verification, download and export append per-evidence custody entries to a SHA-256-linked chain. Legal-hold records can be placed and released with audit events. Neither feature is a substitute for object-lock/WORM retention, external signatures or storage-level deletion enforcement.
