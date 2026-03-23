import pytest
from neutrino.loki.logql import build_query


def test_no_filters():
    assert build_query() == '{job=~".+"}'


def test_service_only():
    assert build_query(service="payments") == '{service="payments"}'


def test_service_and_severity_error():
    q = build_query(service="payments", severity="error")
    assert q.startswith('{service="payments"}')
    assert "level=~" in q
    assert "error" in q


def test_severity_warn_includes_error():
    q = build_query(severity="warn")
    assert "warn" in q
    assert "error" in q


def test_unknown_severity_ignored():
    q = build_query(service="api", severity="unknown")
    assert q == '{service="api"}'
