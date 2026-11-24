-- ORACLE CONTROL initial managed PostgreSQL schema.
-- Applied to Supabase project zkxoknpwcleicomxfrwi on 2026-11-24.
-- Tables are intentionally not granted to anon/authenticated; the API uses a
-- private server-side PostgreSQL connection and enforces tenant scope.
-- This schema is not an immutable/WORM evidence archive.

create table if not exists public.events (
  id serial primary key, tenant_id varchar(128) not null, event_id varchar(256) not null,
  source_system varchar(256) not null, source_event_id varchar(256) not null,
  event_type varchar(256) not null, occurred_at timestamptz not null, ingested_at timestamptz not null,
  agent_id varchar(256), run_id varchar(256), session_id varchar(256), parent_agent_id varchar(256),
  parent_run_id varchar(256), credential_ref varchar(256), actor_id varchar(256),
  resource_id varchar(1024), confidence varchar(32) not null, payload json not null,
  payload_sha256 varchar(64) not null, event_sha256 varchar(64) not null,
  redaction_applied boolean not null default false
);
create unique index if not exists uq_event_tenant_event on public.events(tenant_id,event_id);
create index if not exists ix_events_tenant_id on public.events(tenant_id);
create index if not exists ix_events_occurred_at on public.events(occurred_at);
create index if not exists ix_event_tenant_time on public.events(tenant_id,occurred_at);
create index if not exists ix_events_agent_id on public.events(agent_id);
create index if not exists ix_events_run_id on public.events(run_id);
create index if not exists ix_events_session_id on public.events(session_id);
create index if not exists ix_events_parent_agent_id on public.events(parent_agent_id);
create index if not exists ix_events_parent_run_id on public.events(parent_run_id);

create table if not exists public.cases (
  id varchar(36) primary key, tenant_id varchar(128) not null, title varchar(300) not null,
  description text not null, agent_ids json not null default '[]'::json,
  severity varchar(16) not null, status varchar(24) not null, created_by varchar(256) not null,
  created_at timestamptz not null, updated_at timestamptz not null
);
create index if not exists ix_cases_tenant_id on public.cases(tenant_id);
create index if not exists ix_case_tenant_status on public.cases(tenant_id,status);

create table if not exists public.findings (
  id varchar(36) primary key, case_id varchar(36) not null references public.cases(id) on delete cascade,
  tenant_id varchar(128) not null, title varchar(300) not null, statement text not null,
  confidence varchar(32) not null, evidence_ids json not null default '[]'::json,
  created_at timestamptz not null
);
create index if not exists ix_findings_case_id on public.findings(case_id);
create index if not exists ix_findings_tenant_id on public.findings(tenant_id);

create table if not exists public.evidence (
  id varchar(36) primary key, tenant_id varchar(128) not null,
  case_id varchar(36) references public.cases(id), filename varchar(512) not null,
  media_type varchar(256) not null, storage_path text not null, byte_length integer not null,
  sha256 varchar(64) not null, source_system varchar(256) not null,
  source_reference varchar(512), collected_by varchar(256) not null,
  collected_at timestamptz not null, metadata_json json not null default '{}'::json
);
create index if not exists ix_evidence_tenant_id on public.evidence(tenant_id);
create index if not exists ix_evidence_case_id on public.evidence(case_id);
create index if not exists ix_evidence_sha256 on public.evidence(sha256);

create table if not exists public.audit_log (
  id serial primary key, tenant_id varchar(128) not null, actor varchar(256) not null,
  action varchar(128) not null, object_type varchar(64) not null, object_id varchar(256) not null,
  details json not null default '{}'::json, occurred_at timestamptz not null
);
create index if not exists ix_audit_log_tenant_id on public.audit_log(tenant_id);

create table if not exists public.agents (
  id serial primary key, tenant_id varchar(128) not null, agent_id varchar(256) not null,
  display_name varchar(256) not null, framework varchar(128), environment varchar(128),
  owner varchar(256), status varchar(32) not null, metadata_json json not null default '{}'::json,
  created_at timestamptz not null, updated_at timestamptz not null,
  constraint uq_agent_tenant_agent unique(tenant_id,agent_id)
);
create index if not exists ix_agents_tenant_id on public.agents(tenant_id);

create table if not exists public.authority_records (
  id varchar(36) primary key, tenant_id varchar(128) not null, agent_id varchar(256) not null,
  principal_id varchar(256) not null, permission varchar(256) not null,
  resource_scope varchar(1024) not null, decision varchar(24) not null,
  source_system varchar(128) not null, approval_reference varchar(256),
  valid_from timestamptz not null, valid_until timestamptz,
  evidence_ids json not null default '[]'::json, created_at timestamptz not null
);
create index if not exists ix_authority_records_tenant_id on public.authority_records(tenant_id);
create index if not exists ix_authority_records_agent_id on public.authority_records(agent_id);

create table if not exists public.approvals (
  id varchar(36) primary key, tenant_id varchar(128) not null, agent_id varchar(256) not null,
  approver_id varchar(256) not null, action varchar(256) not null,
  resource_scope varchar(1024) not null, decision varchar(24) not null,
  source_system varchar(128) not null, source_reference varchar(256),
  decided_at timestamptz not null, evidence_ids json not null default '[]'::json
);
create index if not exists ix_approvals_tenant_id on public.approvals(tenant_id);

create table if not exists public.custody_records (
  id serial primary key, tenant_id varchar(128) not null,
  evidence_id varchar(36) not null references public.evidence(id), actor varchar(256) not null,
  action varchar(64) not null, details json not null default '{}'::json,
  previous_hash varchar(64) not null, record_hash varchar(64) not null, occurred_at timestamptz not null
);
create index if not exists ix_custody_records_tenant_id on public.custody_records(tenant_id);
create index if not exists ix_custody_records_evidence_id on public.custody_records(evidence_id);
create index if not exists ix_custody_records_record_hash on public.custody_records(record_hash);
create index if not exists ix_custody_tenant_evidence on public.custody_records(tenant_id,evidence_id,id);

create table if not exists public.legal_holds (
  id varchar(36) primary key, tenant_id varchar(128) not null,
  case_id varchar(36) not null references public.cases(id),
  evidence_id varchar(36) references public.evidence(id), reason text not null,
  status varchar(24) not null, placed_by varchar(256) not null, released_by varchar(256),
  created_at timestamptz not null, released_at timestamptz
);
create index if not exists ix_legal_holds_tenant_id on public.legal_holds(tenant_id);
create index if not exists ix_legal_holds_case_id on public.legal_holds(case_id);
create index if not exists ix_legal_holds_evidence_id on public.legal_holds(evidence_id);

do $$
declare t text;
begin
  foreach t in array array[
    'events','cases','findings','evidence','audit_log','agents','authority_records',
    'approvals','custody_records','legal_holds'
  ] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on table public.%I from anon, authenticated', t);
  end loop;
end $$;
do $
declare t text;
begin
  foreach t in array array[
    'events','cases','findings','evidence','audit_log','agents','authority_records',
    'approvals','custody_records','legal_holds'
  ] loop
    execute format('drop policy if exists deny_supabase_data_api_roles on public.%I', t);
    execute format('create policy deny_supabase_data_api_roles on public.%I for all to anon, authenticated using (false) with check (false)', t);
  end loop;
end $;
revoke all on all sequences in schema public from anon, authenticated;
