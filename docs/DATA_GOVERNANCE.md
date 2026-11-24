# Data governance and minimisation

## Data classes
- Identity metadata: tenant, agent, actor, principal and opaque credential references.
- Operational telemetry: event type, source ID, timestamps, run/session and resource references.
- Sensitive event payloads: tool inputs/outputs and source-specific request metadata.
- Evidence originals: uploaded bytes and source-provided records.
- Derived analysis: correlations, risk indicators and AI-generated drafts.
- Case content: analyst findings, approvals, notes and legal-hold reasons.

## Collection rules
- Collect the minimum operational data needed to investigate.
- Never collect model chain-of-thought.
- Never send credentials or secret values as credential references.
- Use explicit allowlists for telemetry attributes and document omitted fields.
- Redact sensitive values before indexing or forwarding to model providers.
- Treat source records as untrusted input; preserve provenance and parsing failures.

## Model-provider egress
The investigation model adapter is disabled by default. Enabling it sends the selected case context to the configured OpenAI-compatible endpoint. The default request excludes event payloads. Customers must review provider location, retention, training policy, contractual terms and data residency before enabling it. A private endpoint can be configured for customer-controlled deployments.

## Retention and deletion
Retention periods, deletion schedules, legal holds and jurisdictional requirements must be tenant-configurable before production. The current legal-hold API records intent and lifecycle but does not enforce storage-level retention or deletion locks. Do not treat the local evidence volume as immutable storage.

## Access and audit
API keys are mapped to one tenant and role set. Evidence reads/downloads, verification, exports and case changes generate audit/custody records. Audit and custody records are not yet externally anchored; a privileged database administrator could rewrite stored history.
