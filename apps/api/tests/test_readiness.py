from fastapi import Response

from oracle_control import readiness


def test_readiness_reports_ready_without_exposing_configuration(monkeypatch):
    monkeypatch.setattr(readiness, "_database_check", lambda: "ok")
    monkeypatch.setattr(readiness, "_storage_check", lambda: "ok")
    response = Response()
    result = readiness.system_readiness(response, {"roles": ["admin"]})
    assert response.status_code == 200
    assert result["status"] == "ready"
    assert result["checks"] == {"database": "ok", "evidence_storage": "ok"}
    assert "password" not in str(result).lower()
    assert "key" not in str(result).lower()


def test_readiness_marks_degraded_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(readiness, "_database_check", lambda: "unavailable")
    monkeypatch.setattr(readiness, "_storage_check", lambda: "ok")
    response = Response()
    result = readiness.system_readiness(response, {"roles": ["admin"]})
    assert response.status_code == 503
    assert result["status"] == "degraded"
    assert result["checks"]["database"] == "unavailable"


def test_readiness_marks_degraded_when_storage_is_unavailable(monkeypatch):
    monkeypatch.setattr(readiness, "_database_check", lambda: "ok")
    monkeypatch.setattr(readiness, "_storage_check", lambda: "unavailable")
    response = Response()
    result = readiness.system_readiness(response, {"roles": ["admin"]})
    assert response.status_code == 503
    assert result["status"] == "degraded"
    assert result["checks"]["evidence_storage"] == "unavailable"
