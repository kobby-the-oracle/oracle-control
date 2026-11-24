export type AgentEvent = {
  event_id: string;
  tenant_id?: string;
  source: { system: string; event_id: string; schema_version?: string };
  event_type: string;
  occurred_at: string;
  agent_id?: string | null;
  run_id?: string | null;\n  session_id?: string | null;\n  parent_agent_id?: string | null;\n  parent_run_id?: string | null;\n  credential_ref?: string | null;
  actor_id?: string | null;
  resource_id?: string | null;
  relationship_confidence?: "directly_observed" | "correlated" | "inferred" | "unknown";
  payload: Record<string, unknown>;
  redaction_applied?: boolean;
};

export class OracleControlClient {
  constructor(
    private readonly baseUrl: string,
    private readonly apiKey: string,
    private readonly tenantId: string,
  ) {}

  async emit(event: AgentEvent): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl.replace(/\/$/, "")}/v1/events`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": this.apiKey,
      },
      body: JSON.stringify({ ...event, tenant_id: this.tenantId }),
    });
    if (!response.ok) {
      throw new Error(`ORACLE CONTROL API ${response.status}: ${await response.text()}`);
    }
    return response.json() as Promise<Record<string, unknown>>;
  }
}
