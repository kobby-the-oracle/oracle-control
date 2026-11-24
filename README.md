# ORACLE CONTROL

Evidence-centred AI incident investigation and digital forensics.

ORACLE CONTROL helps organisations investigate activity performed by AI agents across connected systems: what happened, which identity and authority were involved, what resources were affected, what evidence supports each conclusion, and what remains unknown.

**Forensic integrity rule:** a hash proves collected bytes have not changed since hashing. It does not prove source records were truthful or collection was complete.

## Core investigation workflow
1. Ingest structured agent activity with source provenance.
2. Preserve originals and normalise queryable events.
3. Correlate agents, runs, actors, tools, approvals and resources.
4. Build an evidence-linked incident timeline.
5. Verify evidence integrity and export a case manifest.
6. Enforce tenant boundaries, access controls and audit trails.

## Repository
- `apps/api` — FastAPI ingestion and investigation API.
- `apps/web` — React enterprise console.
- `packages/schemas` — versioned event contract.
- `docs` — product, architecture and security specifications.
- `infra` — local deployment assets.

## Status
This is an initial engineering foundation, not a production-ready enterprise platform. Persistent storage, tenant-aware authentication, hardened evidence retention, production connectors, full case workflows and deployment hardening remain to be implemented.

## Local API
Python 3.11+:
```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn oracle_control.main:app --reload
```
OpenAPI docs: http://localhost:8000/docs
