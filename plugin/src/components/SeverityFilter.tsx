import React from 'react';
import { Select } from '@grafana/ui';
import { SelectableValue } from '@grafana/data';

const SEVERITY_OPTIONS: Array<SelectableValue<string>> = [
  { label: 'Any', value: '' },
  { label: 'Debug+', value: 'debug' },
  { label: 'Info+', value: 'info' },
  { label: 'Warn+', value: 'warn' },
  { label: 'Error+', value: 'error' },
];

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export function SeverityFilter({ value, onChange }: Props) {
  return (
    <Select
      options={SEVERITY_OPTIONS}
      value={value || ''}
      onChange={(sel) => onChange(sel?.value ?? '')}
      width={16}
    />
  );
}
