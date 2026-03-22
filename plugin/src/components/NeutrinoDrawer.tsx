import React, { useState } from 'react';
import { RawTimeRange, dateTimeParse } from '@grafana/data';
import { Alert, HorizontalGroup } from '@grafana/ui';
import { ServiceSelector } from './ServiceSelector';
import { SeverityFilter } from './SeverityFilter';
import { QueryInput } from './QueryInput';
import { ResultsList } from './ResultsList';
import { search } from '../api';
import type { LogResult } from '../types';

interface Props {
  timeRange?: RawTimeRange;
  datasourceUid?: string;
  onDismiss?: () => void;
}

function toNs(raw: string | number | undefined): number {
  if (!raw) {
    return Date.now() * 1_000_000;
  }
  return dateTimeParse(raw).valueOf() * 1_000_000;
}

export function NeutrinoDrawer({ timeRange, datasourceUid, onDismiss }: Props) {
  const [service, setService] = useState<string | undefined>(undefined);
  const [severity, setSeverity] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<LogResult[]>([]);
  const [totalFetched, setTotalFetched] = useState(0);
  const [error, setError] = useState<string | undefined>(undefined);

  const handleSearch = async (query: string) => {
    setLoading(true);
    setError(undefined);

    try {
      const resp = await search({
        query,
        service: service || undefined,
        severity: severity || undefined,
        start_ns: toNs(timeRange?.from as string | number | undefined),
        end_ns: toNs(timeRange?.to as string | number | undefined),
      });
      setResults(resp.results);
      setTotalFetched(resp.total_fetched);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!timeRange) {
    return <Alert title="No time range" severity="error">Neutrino requires a time range. Set one in the Explore toolbar and try again.</Alert>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, padding: 8 }}>
      <HorizontalGroup>
        <ServiceSelector value={service} onChange={setService} />
        <SeverityFilter value={severity} onChange={setSeverity} />
      </HorizontalGroup>

      <QueryInput onSearch={handleSearch} loading={loading} />

      <ResultsList
        results={results}
        totalFetched={totalFetched}
        datasourceUid={datasourceUid ?? ''}
        error={error}
      />
    </div>
  );
}
