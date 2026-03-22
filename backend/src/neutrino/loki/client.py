import httpx
from typing import Optional
from neutrino.config import settings
from neutrino.loki.logql import build_query


class LokiClient:
    def __init__(self, base_url: str = settings.loki_url):
        self._base_url = base_url.rstrip("/")

    async def query_range(
        self,
        start_ns: int,
        end_ns: int,
        service: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = settings.max_log_lines,
    ) -> list[tuple[int, dict[str, str], str]]:
        """
        Fetch log lines from Loki.

        Returns list of (timestamp_ns, labels, line).
        """
        logql = build_query(service=service, severity=severity)

        params = {
            "query": logql,
            "start": str(start_ns),
            "end": str(end_ns),
            "limit": str(limit),
            "direction": "backward",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self._base_url}/loki/api/v1/query_range",
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        results: list[tuple[int, dict[str, str], str]] = []
        for stream in data.get("data", {}).get("result", []):
            labels: dict[str, str] = stream.get("stream", {})
            for ts_str, line in stream.get("values", []):
                results.append((int(ts_str), labels, line))

        return results

    async def label_values(self, label: str) -> list[str]:
        """Fetch all values for a given label from Loki."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._base_url}/loki/api/v1/label/{label}/values",
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("data", [])
