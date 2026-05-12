import json

from src.api import observability


def test_resolve_route_metadata():
    assert observability.resolve_route_metadata("/api/patients/raw", "GET") == (
        "patient_data",
        "read",
    )
    assert observability.resolve_route_metadata("/api/metrics/aggregated", "GET") == (
        "aggregated_metrics",
        "read",
    )
    assert observability.resolve_route_metadata("/health", "GET") == (None, None)


def test_record_audit_event_writes_json_line(tmp_path, monkeypatch):
    audit_log = tmp_path / "api_access.log"
    monkeypatch.setattr(observability, "AUDIT_LOG_PATH", audit_log)
    observability.reset_observability_state()

    event = observability.record_audit_event(
        request_id="req-123",
        method="GET",
        path="/api/patients/raw",
        user="alice",
        role="admin",
        resource="patient_data",
        action="read",
        status_code=200,
        duration_ms=12.34,
    )

    assert event["request_id"] == "req-123"
    assert audit_log.exists()
    payload = json.loads(audit_log.read_text(encoding="utf-8").strip())
    assert payload["role"] == "admin"
    assert payload["status_code"] == 200


def test_render_prometheus_metrics_reflects_events(tmp_path, monkeypatch):
    audit_log = tmp_path / "api_access.log"
    monkeypatch.setattr(observability, "AUDIT_LOG_PATH", audit_log)
    observability.reset_observability_state()

    observability.record_audit_event(
        request_id="req-456",
        method="GET",
        path="/api/patients/raw",
        user="bob",
        role="ml_engineer",
        resource="patient_data",
        action="read",
        status_code=403,
        duration_ms=8.0,
    )

    metrics = observability.render_prometheus_metrics()
    assert 'medviet_http_requests_total{method="GET",path="/api/patients/raw"} 1' in metrics
    assert 'medviet_http_responses_total{status_code="403"} 1' in metrics
    assert "medviet_unauthorized_raw_access_total 1" in metrics
