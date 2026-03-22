from typing import Optional


_SEVERITY_MAP = {
    "error": ["error", "err", "critical", "crit", "fatal"],
    "warn": ["warn", "warning", "error", "err", "critical", "crit", "fatal"],
    "info": ["info", "warn", "warning", "error", "err", "critical", "crit", "fatal"],
    "debug": ["debug", "info", "warn", "warning", "error", "err", "critical", "crit", "fatal"],
}


def build_query(
    service: Optional[str] = None,
    severity: Optional[str] = None,
) -> str:
    """Build a LogQL stream selector from optional filters."""
    selectors: list[str] = []

    if service:
        selectors.append(f'service="{service}"')

    if selectors:
        stream = "{" + ", ".join(selectors) + "}"
    else:
        stream = "{}"

    pipeline_parts: list[str] = []

    if severity and severity.lower() in _SEVERITY_MAP:
        levels = _SEVERITY_MAP[severity.lower()]
        level_pattern = "|".join(levels)
        pipeline_parts.append(f'level=~"(?i)({level_pattern})"')

    if pipeline_parts:
        return stream + " | " + " | ".join(pipeline_parts)
    return stream
