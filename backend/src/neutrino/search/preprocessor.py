import re

# ISO 8601 / common log timestamps
_RE_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)

# UUIDs (8-4-4-4-12)
_RE_UUID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)

# IPv4 addresses
_RE_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")

# Numeric IDs in URL paths (e.g. /users/1234/orders)
_RE_PATH_ID = re.compile(r"((?:/[a-zA-Z_-]+)+)/\d+")

# Hex strings that look like request IDs (>=8 hex chars)
_RE_HEX_ID = re.compile(r"\b[0-9a-fA-F]{8,}\b")

# Whitespace normalization
_RE_WHITESPACE = re.compile(r"[\s\x00-\x1f]+")


def preprocess(line: str) -> str:
    """Normalize a log line before embedding."""
    line = _RE_TIMESTAMP.sub("", line)
    line = _RE_UUID.sub("<ID>", line)
    line = _RE_IP.sub("<IP>", line)
    line = _RE_PATH_ID.sub(r"\1/<ID>", line)
    line = _RE_HEX_ID.sub("<ID>", line)
    line = _RE_WHITESPACE.sub(" ", line)
    return line.strip()
