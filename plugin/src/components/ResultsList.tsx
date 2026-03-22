import React from 'react';
import { dateTimeFormat } from '@grafana/data';
import { Alert, Badge, LinkButton } from '@grafana/ui';
import type { LogResult } from '../types';
import { buildExploreUrl } from '../utils/logql';

interface Props {
  results: LogResult[];
  totalFetched: number;
  datasourceUid: string;
  error?: string;
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color = pct >= 85 ? 'green' : pct >= 70 ? 'orange' : 'red';
  return (
    <Badge text={`${pct}%`} color={color} tooltip={`Similarity score: ${score.toFixed(3)}`} />
  );
}

function LabelChips({ labels }: { labels: Record<string, string> }) {
  return (
    <span style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
      {Object.entries(labels).map(([k, v]) => (
        <code key={k} style={{ fontSize: 11, opacity: 0.75 }}>
          {k}=&quot;{v}&quot;
        </code>
      ))}
    </span>
  );
}

export function ResultsList({ results, totalFetched, datasourceUid, error }: Props) {
  if (error) {
    return <Alert title="Search failed" severity="error">{error}</Alert>;
  }

  if (results.length === 0 && totalFetched === 0) {
    return null;
  }

  if (results.length === 0) {
    return (
      <Alert title="No results" severity="info">
        Searched {totalFetched.toLocaleString()} log lines — no matches found.
      </Alert>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 8, opacity: 0.6, fontSize: 12 }}>
        Top {results.length} of {totalFetched.toLocaleString()} log lines
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {results.map((result, i) => {
          const tsMs = Math.floor(result.timestamp_ns / 1_000_000);
          const timestamp = dateTimeFormat(tsMs, { format: 'HH:mm:ss.SSS' });
          const exploreUrl = buildExploreUrl(result, datasourceUid);

          return (
            <div
              key={i}
              style={{
                padding: '10px 12px',
                borderRadius: 4,
                border: '1px solid rgba(255,255,255,0.07)',
                display: 'flex',
                flexDirection: 'column',
                gap: 4,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ScoreBadge score={result.score} />
                <span style={{ fontFamily: 'monospace', fontSize: 12, opacity: 0.75 }}>
                  {timestamp}
                </span>
                <LabelChips labels={result.labels} />
                <LinkButton
                  href={exploreUrl}
                  size="sm"
                  variant="secondary"
                  icon="arrow-right"
                  style={{ marginLeft: 'auto' }}
                >
                  View in LogQL
                </LinkButton>
              </div>
              <code style={{ fontSize: 12, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {result.line}
              </code>
            </div>
          );
        })}
      </div>
    </div>
  );
}
