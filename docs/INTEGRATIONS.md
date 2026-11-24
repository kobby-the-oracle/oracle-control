# Integration programme and connector contract

## Design
Connectors are source adapters, not agents that silently alter evidence. Every connector must:
- Authenticate to the source with least-privilege, read-only scopes wherever possible.
- Preserve source event IDs, source timestamps, source system and collector identity.
- Preserve original source material or a retrievable source reference according to tenant policy.
- Emit the common event envelope and classify relationships as observed/correlated/inferred/unknown.
- Expose cursor/checkpoint, retry, rate-limit, backfill, health and last-success metadata.
- Redact secrets and high-risk content before indexing; document what is omitted.
- Make collection gaps and API permission failures visible.

## Initial adapter code
- OpenTelemetry span adapter and authenticated batch-ingest endpoint: implemented for pushed span JSON; no OTLP network receiver, live collector fleet or production polling/checkpoint service yet.
- AWS CloudTrail record adapter and authenticated batch-ingest endpoint: implemented for pushed records; no AWS credentialed polling, EventBridge/SQS subscription or historical backfill service yet.

## First-party SDKs
Python and TypeScript SDK packages can emit canonical agent events to the tenant API. They require the caller to supply stable event IDs and to redact sensitive payloads. They are transport clients, not runtime auto-instrumentation packages.

## Connector roadmap and status
| Source family | Planned systems | Status |
|---|---|---|
| Agent telemetry | OpenTelemetry, LangChain/LangGraph, OpenAI-compatible agent traces, custom SDK | Adapter prototypes only |
| Cloud audit | AWS CloudTrail, Azure Activity, Google Cloud Audit Logs | AWS record mapper prototype |
| Identity | Entra ID, Okta, Google Workspace, AWS IAM | Planned |
| Endpoint/security | Microsoft Defender, CrowdStrike, SentinelOne, Splunk, Elastic | Planned |
| Data platforms | PostgreSQL, Snowflake, BigQuery, S3 | Planned |
| SaaS/workflow | GitHub, Jira, Slack, ServiceNow, Salesforce | Planned |
| Response | SIEM/SOAR and ticketing platforms | Planned |

Do not market roadmap entries as working connectors. Each connector graduates only after integration tests against a real test tenant, checkpoint/retry tests, permission-scope review, data-minimisation review and documented operational runbook.

## Canonical event contract
Required: tenant_id, event_id, source.system, source.event_id, event_type, occurred_at, payload.
Optional identity/context: agent_id, run_id, actor_id, resource_id.
Required semantics: source timestamp is not ingestion timestamp; preserve both. Never infer causality from timestamp proximity alone.
