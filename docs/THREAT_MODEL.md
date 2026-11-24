# Threat model

## Assets
- Original evidence and evidence metadata.
- Agent activity events and identity/authority relationships.
- Investigation cases, findings and analyst notes.
- API credentials, database credentials and encryption keys.
- Tenant configuration, retention and legal-hold records.
- Connector checkpoints and source credentials.

## Trust boundaries
1. Customer source systems and agent runtimes.
2. Collector processes and connector credentials.
3. Public/API ingress and tenant authentication.
4. Normalised event and evidence storage.
5. Derived analysis and optional model-provider egress.
6. Analyst browser and export destinations.
7. Database/object-store administrators.

## Threats and controls
| Threat | Current / required control |
|---|---|
| Cross-tenant data access | Tenant ID derived from authenticated principal; tenant filters on API queries; automated isolation tests |
| Forged or replayed event | Source event identity, idempotent event ID and conflict rejection; source authenticity still depends on connector trust |
| Evidence modified after collection | SHA-256 digest, verification endpoint and case export re-verification |
| Custody record edited | Per-evidence hash chain; external WORM/signature anchoring remains required |
| Malicious or compromised collector | Least-privilege read-only credentials, collector identity, rotation and revocation required before production |
| Sensitive prompt/tool data leakage | Allowlisted OpenTelemetry attributes; CloudTrail body omission; avoid chain-of-thought; tenant redaction policy still needs expansion |
| Model prompt injection / fabricated claims | Model output is a draft; citation IDs validated; no automatic action; full adversarial evaluation still required |
| API key theft | Secret-manager storage, rotation, TLS, scoped roles and OIDC migration required |
| Malicious file upload | Size limit and filename sanitisation exist; malware scanning and content-type validation remain required |
| Database administrator rewrites audit/custody | External immutable anchoring, WORM and signed manifests remain required |
| Model-provider data egress | Model disabled by default; explicit provider configuration; customer-controlled/private model option required |
| Service outage or data loss | Persistent database and evidence volume; production backup, restore and disaster-recovery controls remain required |

## Current security boundary
API-key tenant mapping and role checks are bootstrap controls, not a complete enterprise identity platform. There is no production OIDC/SAML, SCIM, customer-managed KMS, object-lock enforcement, formal penetration-test result or external audit-chain anchoring in this repository yet.

## Security release gates
- Threat modelling and privacy review for each connector.
- Tenant isolation tests for every resource type.
- Secret scanning, dependency scanning and container scanning.
- Authentication and authorisation review.
- Upload scanning and size/rate limits.
- Restore and incident-response exercises.
- Independent penetration test before production claims.
