import React, { useState } from 'react';
import { Button, Input } from '@grafana/ui';

interface Props {
  onSearch: (query: string) => void;
  loading: boolean;
}

export function QueryInput({ onSearch, loading }: Props) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSearch(value.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
      <Input
        placeholder='Search logs by meaning — e.g. "database connection issues"'
        value={value}
        onChange={(e) => setValue(e.currentTarget.value)}
        width={60}
      />
      <Button type="submit" icon="search" disabled={loading || !value.trim()}>
        {loading ? 'Searching…' : 'Search'}
      </Button>
    </form>
  );
}
