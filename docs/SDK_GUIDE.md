# Agent SDK guide

## Python
Install from the repository:

```bash
pip install -e packages/python-sdk
```

Example:

```python
from oracle_control_sdk import OracleControlClient

with OracleControlClient(
    base_url="https://your-oracle-control-host",
    api_key="YOUR_TENANT_API_KEY",
    tenant_id="your-tenant",
) as oracle:
    oracle.emit_tool_invocation(
        event_id="stable-unique-event-id",
        source_event_id="framework-event-id",
        occurred_at="2026-11-24T12:00:00Z",
        agent_id="research-agent-01",
        run_id="run-123",
        tool_name="document.search",
        resource_id="knowledge-base/project-alpha",
        outcome="success",
    )
```

## TypeScript
Build the package:

```bash
cd packages/typescript-sdk
npm install
npm run build
```

Example:

```ts
import { OracleControlClient } from "@oracle-control/sdk";

const oracle = new OracleControlClient(
  "https://your-oracle-control-host",
  process.env.ORACLE_CONTROL_API_KEY!,
  "your-tenant",
);

await oracle.emit({
  event_id: crypto.randomUUID(),
  source: { system: "my-agent-runtime", event_id: "span-or-event-id" },
  event_type: "tool.invoked",
  occurred_at: new Date().toISOString(),
  agent_id: "research-agent-01",
  run_id: "run-123",
  relationship_confidence: "directly_observed",
  payload: { tool_name: "document.search", outcome: "success" },
});
```

Use stable event IDs when retrying. The server treats identical tenant/event replays as idempotent and rejects conflicting content. Never send model chain-of-thought, credentials, secrets or unnecessary personal data. Redact sensitive tool inputs and outputs before emission.
