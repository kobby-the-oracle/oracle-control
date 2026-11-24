# ORACLE CONTROL validation plan

## Product hypotheses to test
1. Security and forensic teams need an independent record of agent actions across vendors and systems.
2. Investigators value historical identity/authority context and human approval provenance, not only trace visualisation.
3. Evidence integrity, collection-gap visibility and exportable case records are important enough to justify a separate product budget.
4. Customers will permit collection only when scopes, redaction, retention, tenancy and deployment boundaries are clear.

These are hypotheses, not proven market gaps.

## Customer discovery
Conduct 30–40 interviews across:
- Regulated enterprises (banking, insurance, healthcare, public sector).
- AI-native companies operating agents in production.
- Incident response, security operations and digital forensics.
- AI platform engineering, internal audit, privacy and legal.

Ask for recent real incidents, current investigation steps, sources of truth, evidence retention, authority/approval gaps, procurement owners, deployment restrictions and budget. Do not lead with a feature pitch.

## Controlled forensic scenario
Use a synthetic scenario in a customer-approved sandbox:
1. An agent receives a legitimate task and a scoped identity.
2. A permission change occurs.
3. The agent invokes a tool to read a sensitive resource.
4. A human approval is recorded or missing.
5. The agent attempts an outbound transfer.
6. Some source records are intentionally delayed or unavailable.

Measure whether the platform can reconstruct the timeline, actor/agent identity, authority state, affected resource and collection gaps without presenting inferred causality as fact.

## Technical validation
- Duplicate and out-of-order ingestion.
- Clock skew and source/ingestion timestamp distinction.
- Cross-tenant access attempts.
- Missing, partial and malformed source records.
- Evidence tampering after collection.
- Case export reproducibility and digest verification.
- Custody chain edits and full-chain rewrite threat.
- Connector permission scope and credential revocation.
- Backfill/retry and checkpoint correctness when live connectors are introduced.
- Private deployment with outbound network disabled.

## Suggested design-partner programme
Recruit 2–3 design partners with named incident-response owners and a real test environment. Prefer a paid pilot or written budget-backed commitment over positive feedback alone.

## Proposed success measures
These are internal targets to test, not industry benchmarks:
- An investigator can produce a cited incident timeline without manual spreadsheet reconstruction.
- Every material conclusion has evidence references or an explicit evidence gap.
- Conflicting event replay is rejected; identical replay is idempotent.
- Cross-tenant API tests fail closed.
- Evidence digest verification detects post-collection modification.
- Connector failure and collection lag are visible to an operator.
- A customer security review can identify data flows, key custody, retention and egress.

## 90-day validation sequence
- Days 1–15: interviews, workflow mapping, competitor bake-off and initial threat model.
- Days 16–30: controlled ingestion and evidence integrity proof.
- Days 31–60: complete one end-to-end incident workflow with case export and custody.
- Days 61–90: design-partner trials, deployment review, willingness-to-pay and release decision.

## Stop / pivot criteria
Reconsider positioning if target customers consistently solve the problem with existing SIEM/observability/agent platforms, cannot provide required source data, will not permit evidence collection, or do not assign a budget owner to cross-system agent forensics.
