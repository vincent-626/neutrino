import type { LogResult } from '../types';

/**
 * Build a "View in LogQL" Grafana Explore URL for a specific log result.
 *
 * Navigates to the Explore page with a LogQL query scoped to the exact
 * stream labels of the result, with the time window narrowed to ±2 minutes
 * around the result timestamp.
 */
export function buildExploreUrl(
  result: LogResult,
  datasourceUid: string
): string {
  const labels = result.labels;
  const selector =
    '{' +
    Object.entries(labels)
      .map(([k, v]) => `${k}="${v}"`)
      .join(', ') +
    '}';

  const tsMs = Math.floor(result.timestamp_ns / 1_000_000);
  const fromMs = tsMs - 2 * 60 * 1000;
  const toMs = tsMs + 2 * 60 * 1000;

  const panes = {
    neu: {
      datasource: datasourceUid,
      queries: [{ refId: 'A', expr: selector, datasource: { uid: datasourceUid } }],
      range: { from: String(fromMs), to: String(toMs) },
    },
  };

  const params = new URLSearchParams({
    orgId: '1',
    schemaVersion: '1',
    panes: JSON.stringify(panes),
  });

  return `/explore?${params.toString()}`;
}
