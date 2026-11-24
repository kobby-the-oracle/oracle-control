import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from oracle_control.db import Base, get_db
from oracle_control.main import app

@pytest.fixture()
def client(monkeypatch):
    test_engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    TestingSession=sessionmaker(bind=test_engine,autoflush=False,autocommit=False)
    Base.metadata.create_all(bind=test_engine)
    def override_db():
        db=TestingSession()
        try: yield db
        finally: db.close()
    app.dependency_overrides[get_db]=override_db
    import oracle_control.security as security
    monkeypatch.setattr(security,"API_KEYS",{"test-secret":"tenant-demo"})
    with TestClient(app) as test_client:
        test_client.headers.update({"X-API-Key":"test-secret"})
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()

def sample_event(tenant="tenant-demo"):
    return {"event_id":"evt-001","tenant_id":tenant,
        "source":{"system":"demo-agent","event_id":"src-001"},
        "event_type":"tool.invoked","occurred_at":"2026-11-24T01:00:00Z",
        "agent_id":"agent-7","run_id":"run-42","session_id":"session-5",
        "parent_agent_id":"orchestrator-1","parent_run_id":"run-parent","credential_ref":"credref-17","actor_id":"user-3",
        "resource_id":"bucket/customer-data","relationship_confidence":"directly_observed",
        "payload":{"tool":"object.read","result":"success"}}

def test_health_is_public(client):
    assert client.get("/health").json()["status"]=="ok"

def test_auth_required():
    with TestClient(app) as c:
        assert c.get("/v1/events").status_code==401

def test_event_ingestion_and_idempotent_replay(client):
    event=sample_event()
    first=client.post("/v1/events",json=event)
    second=client.post("/v1/events",json=event)
    assert first.status_code==201 and second.status_code==200
    assert first.json()["canonical_event_sha256"]==second.json()["canonical_event_sha256"]
    stored=client.get("/v1/events").json()[0]
    assert stored["session_id"]=="session-5" and stored["parent_agent_id"]=="orchestrator-1"

def test_conflicting_event_replay_rejected(client):
    event=sample_event()
    assert client.post("/v1/events",json=event).status_code==201
    event["payload"]["result"]="different"
    assert client.post("/v1/events",json=event).status_code==409

def test_tenant_mismatch_rejected(client):
    assert client.post("/v1/events",json=sample_event("another-tenant")).status_code==403

def test_case_and_finding_workflow(client):
    created=client.post("/v1/cases",json={"title":"Suspicious agent access","severity":"high"})
    assert created.status_code==201
    case_id=created.json()["id"]
    finding=client.post(f"/v1/cases/{case_id}/findings",json={
        "title":"Unexpected object read","statement":"Agent invoked object.read on a sensitive bucket.",
        "confidence":"directly_observed"})
    assert finding.status_code==201
    assert client.get(f"/v1/cases/{case_id}").json()["findings"][0]["confidence"]=="directly_observed"

def test_case_is_tenant_scoped(client):
    created=client.post("/v1/cases",json={"title":"Private tenant case"})
    import oracle_control.security as security
    security.API_KEYS["other-secret"]="other-tenant"
    other=TestClient(app)
    assert other.get(f"/v1/cases/{created.json()['id']}",headers={"X-API-Key":"other-secret"}).status_code==404

def test_agent_authority_and_assistant_workflow(client):
    agent=client.post("/v1/agents",json={"agent_id":"agent-7","display_name":"Research Agent","framework":"langgraph"})
    assert agent.status_code==201
    assert client.get("/v1/agents").json()[0]["agent_id"]=="agent-7"
    authority=client.post("/v1/authority/records",json={
        "agent_id":"agent-7","principal_id":"svc-research","permission":"object.read",
        "resource_scope":"bucket/research","decision":"granted","source_system":"test-idp"})
    assert authority.status_code==201
    case=client.post("/v1/cases",json={"title":"Agent review","agent_ids":["agent-7"]})
    briefing=client.get(f"/v1/intelligence/cases/{case.json()['id']}/briefing")
    assert briefing.status_code==200
    assert briefing.json()["case"]["id"]==case.json()["id"]
    draft=client.post(f"/v1/assistant/cases/{case.json()['id']}/draft",json={})
    assert draft.status_code==200
    assert draft.json()["mode"]=="context-only"

def test_evidence_collection_verification_and_export(client,monkeypatch,tmp_path):
    import oracle_control.storage as storage
    monkeypatch.setattr(storage,"EVIDENCE_DIR",tmp_path)
    case=client.post("/v1/cases",json={"title":"Evidence test"})
    uploaded=client.post("/v1/evidence",data={"case_id":case.json()["id"],"source_system":"test-source"},
        files={"file":("sample.txt",b"forensic sample bytes","text/plain")})
    assert uploaded.status_code==201
    evidence_id=uploaded.json()["id"]
    assert client.post(f"/v1/evidence/{evidence_id}/verify").json()["valid"] is True
    finding=client.post(f"/v1/cases/{case.json()['id']}/findings",json={
        "title":"Sample verified","statement":"Uploaded sample digest verified.","confidence":"directly_observed",
        "evidence_ids":[evidence_id]})
    assert finding.status_code==201
    package=client.get(f"/v1/cases/{case.json()['id']}/export")
    assert package.status_code==200
    assert package.headers["content-type"].startswith("application/zip")
    from io import BytesIO
    import json
    import zipfile
    with zipfile.ZipFile(BytesIO(package.content)) as archive:
        assert "events.json" in archive.namelist()
        manifest=json.loads(archive.read("manifest.json"))
        assert manifest["custody"] and manifest["custody"][0]

def test_role_based_access_blocks_auditor_writes(client):
    import oracle_control.security as security
    security.API_KEYS["auditor-key"]={"tenant_id":"tenant-demo","subject":"audit-user","roles":["auditor"]}
    headers={"X-API-Key":"auditor-key"}
    assert client.get("/v1/cases",headers=headers).status_code==200
    assert client.post("/v1/cases",headers=headers,json={"title":"Should be denied"}).status_code==403

def test_custody_chain_and_legal_hold_lifecycle(client,monkeypatch,tmp_path):
    from oracle_control import storage
    monkeypatch.setattr(storage,"EVIDENCE_DIR",tmp_path)
    case=client.post("/v1/cases",json={"title":"Hold and custody test"})
    evidence=client.post("/v1/evidence",data={"case_id":case.json()["id"]},
        files={"file":("hold.txt",b"preserved bytes","text/plain")})
    evidence_id=evidence.json()["id"]
    chain=client.get(f"/v1/custody/evidence/{evidence_id}")
    assert chain.status_code==200
    assert len(chain.json())==1
    assert client.get(f"/v1/custody/evidence/{evidence_id}/verify").json()["valid"] is True
    transfer=client.post(f"/v1/custody/evidence/{evidence_id}/transfer",
        json={"to_actor":"forensic-reviewer","note":"Assigned for independent review"})
    assert transfer.status_code==201
    assert client.get(f"/v1/custody/evidence/{evidence_id}/verify").json()["valid"] is True
    hold=client.post("/v1/legal-holds",json={"case_id":case.json()["id"],"evidence_id":evidence_id,
        "reason":"Preserve material for an active investigation"})
    assert hold.status_code==201
    assert client.get("/v1/legal-holds").json()[0]["status"]=="active"
    released=client.post(f"/v1/legal-holds/{hold.json()['id']}/release")
    assert released.status_code==200
    assert released.json()["status"]=="released"

def test_connector_batch_ingestion(client):
    cloud=client.post("/v1/connectors/aws/cloudtrail/events",json={"records":[{
        "eventID":"ct-900","eventTime":"2026-11-24T01:00:00Z","eventSource":"s3.amazonaws.com",
        "eventName":"GetObject","awsRegion":"eu-west-1",
        "userIdentity":{"arn":"arn:aws:sts::123:assumed-role/agent/session"},
        "resources":[{"ARN":"arn:aws:s3:::demo-bucket/object"}],
        "requestParameters":{"sensitive":"must-not-be-indexed"}
    }]})
    assert cloud.status_code==200
    assert cloud.json()["results"][0]["status"]=="ingested"
    spans=client.post("/v1/connectors/opentelemetry/spans",json={"spans":[{
        "spanContext":{"traceId":"trace-900","spanId":"span-900"},
        "name":"agent.tool.invoke","startTimeUnixNano":"1795482000000000000",
        "attributes":{"gen_ai.tool.name":"search","oracle.agent.id":"agent-9","prompt":"redact-this"}
    }]})
    assert spans.status_code==200
    assert spans.json()["results"][0]["status"]=="ingested"
    events=client.get("/v1/events").json()
    assert len(events)==2
    assert all("prompt" not in str(e["payload"]) for e in events)

def test_evidence_download_blocks_tampered_bytes(client,monkeypatch,tmp_path):
    import hashlib
    from oracle_control import storage
    monkeypatch.setattr(storage,"EVIDENCE_DIR",tmp_path)
    uploaded=client.post("/v1/evidence",files={"file":("original.txt",b"original bytes","text/plain")})
    evidence_id=uploaded.json()["id"]
    tenant_partition=hashlib.sha256(b"tenant-demo").hexdigest()
    stored=tmp_path/tenant_partition/evidence_id
    stored.write_bytes(b"tampered bytes")
    response=client.get(f"/v1/evidence/{evidence_id}/download")
    assert response.status_code==409

def test_evidence_verification_reports_tampered_bytes(client,monkeypatch,tmp_path):
    import hashlib
    from oracle_control import storage
    monkeypatch.setattr(storage,"EVIDENCE_DIR",tmp_path)
    uploaded=client.post("/v1/evidence",files={"file":("original.txt",b"original bytes","text/plain")})
    assert uploaded.status_code==201
    evidence_id=uploaded.json()["id"]
    tenant_partition=hashlib.sha256(b"tenant-demo").hexdigest()
    stored=tmp_path/tenant_partition/evidence_id
    stored.write_bytes(b"tampered payload with changed length")

    verification=client.post(f"/v1/evidence/{evidence_id}/verify")
    assert verification.status_code==200
    assert verification.json()["valid"] is False
    assert verification.json()["expected_sha256"] != verification.json()["actual_sha256"]

    custody = client.get(f"/v1/custody/evidence/{evidence_id}")
    failed_event = custody.json()[-1]
    assert failed_event["action"] == "evidence.verification_failed"
    assert failed_event["details"]["valid"] is False
    assert failed_event["details"]["expected_sha256"] == verification.json()["expected_sha256"]
    assert failed_event["details"]["actual_sha256"] == verification.json()["actual_sha256"]
    assert failed_event["details"]["expected_byte_length"] != failed_event["details"]["actual_byte_length"]

    download=client.get(f"/v1/evidence/{evidence_id}/download")
    assert download.status_code==409
