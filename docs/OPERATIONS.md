# Operations runbook outline

This repository is not yet a production SRE package. The following runbooks are required before a production launch.

## Service health
- Check `GET /health` for API liveness.
- Check PostgreSQL readiness and connection saturation.
- Monitor evidence-volume capacity and filesystem errors.
- Monitor connector batch failures, source lag and rejected events.
- Alert on repeated authentication failures and cross-tenant access denials.

## Data protection
- Back up PostgreSQL and evidence objects independently.
- Preserve a consistent mapping between evidence metadata and stored object bytes.
- Encrypt backups and restrict restore privileges.
- Perform scheduled restore drills and verify evidence digests after restore.
- Document RPO/RTO per deployment tier.

## Incident response
1. Identify affected tenant, service and time window.
2. Preserve API, database, host and cloud audit logs.
3. Rotate compromised API keys and connector credentials.
4. Record affected evidence IDs and verify digests/custody chains.
5. Notify affected customer contacts under contractual timelines.
6. Preserve incident case exports and document collection gaps.
7. Complete root-cause analysis and corrective actions.

## Connector failure
- Do not silently skip malformed source records.
- Preserve source identifiers and failure reason.
- Retry transient failures with bounded backoff.
- Use stable source event IDs to avoid duplicate ingestion.
- Make cursor position, last successful poll and backfill coverage visible once polling connectors are implemented.
