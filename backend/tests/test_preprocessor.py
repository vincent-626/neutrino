from neutrino.search.preprocessor import preprocess


def test_strips_iso_timestamp():
    line = "2024-01-15T03:22:41Z Failed to connect"
    result = preprocess(line)
    assert "2024" not in result
    assert "Failed to connect" in result


def test_strips_uuid():
    line = "Request a8f3e2b1-0000-0000-0000-000000000000 failed"
    result = preprocess(line)
    assert "a8f3e2b1" not in result
    assert "<ID>" in result


def test_strips_ip():
    line = "Connection from 10.0.4.22 timed out"
    result = preprocess(line)
    assert "10.0.4.22" not in result
    assert "<IP>" in result


def test_normalizes_path_ids():
    line = "GET /api/v2/users/1234/orders"
    result = preprocess(line)
    assert "1234" not in result
    assert "<ID>" in result


def test_collapses_whitespace():
    line = "error\t\t  connecting"
    result = preprocess(line)
    assert "\t" not in result
    assert "  " not in result


def test_preserves_message_content():
    line = "database connection refused"
    result = preprocess(line)
    assert "database connection refused" in result
