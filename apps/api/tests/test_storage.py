from oracle_control import storage


class FakeResponse:
    content = b"private evidence bytes"

    def raise_for_status(self):
        return None


def test_local_storage_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(storage, "EVIDENCE_DIR", tmp_path)
    location = storage.store_evidence("tenant/evidence-1", b"sample", "text/plain")
    assert location == str(tmp_path / "tenant/evidence-1")
    assert storage.read_evidence(location) == b"sample"


def test_supabase_storage_upload_and_download(monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_BACKEND", "supabase")
    monkeypatch.setattr(storage, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(storage, "SUPABASE_SERVICE_ROLE_KEY", "server-only-test-secret")
    monkeypatch.setattr(storage, "SUPABASE_EVIDENCE_BUCKET", "oracle-control-evidence")
    calls = {}

    def fake_post(url, **kwargs):
        calls["post"] = (url, kwargs)
        return FakeResponse()

    def fake_get(url, **kwargs):
        calls["get"] = (url, kwargs)
        return FakeResponse()

    monkeypatch.setattr(storage.httpx, "post", fake_post)
    monkeypatch.setattr(storage.httpx, "get", fake_get)

    location = storage.store_evidence("tenant-a/evidence-1", b"private evidence bytes", "text/plain")
    assert location == "supabase://tenant-a/evidence-1"
    assert calls["post"][1]["headers"]["x-upsert"] == "false"
    assert calls["post"][1]["content"] == b"private evidence bytes"
    assert storage.read_evidence(location) == b"private evidence bytes"
    assert "/oracle-control-evidence/tenant-a/evidence-1" in calls["get"][0]


def test_supabase_storage_requires_server_credentials(monkeypatch):
    monkeypatch.setattr(storage, "SUPABASE_URL", "")
    monkeypatch.setattr(storage, "SUPABASE_SERVICE_ROLE_KEY", "")
    try:
        storage._storage_url("tenant/evidence")
    except storage.EvidenceStorageError as exc:
        assert "credentials" in str(exc)
    else:
        raise AssertionError("missing server credentials must be rejected")
