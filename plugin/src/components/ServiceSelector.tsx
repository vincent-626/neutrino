import React, { useEffect, useState } from 'react';
import { Select } from '@grafana/ui';
import { SelectableValue } from '@grafana/data';
import { getLabelValues } from '../api';

interface Props {
  value: string | undefined;
  onChange: (value: string | undefined) => void;
}

export function ServiceSelector({ value, onChange }: Props) {
  const [options, setOptions] = useState<Array<SelectableValue<string>>>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getLabelValues('service')
      .then((values) => {
        setOptions(values.map((v) => ({ label: v, value: v })));
      })
      .catch(() => {
        // silently fail — selector shows empty
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <Select
      placeholder="All services"
      options={options}
      value={value}
      onChange={(sel) => onChange(sel?.value)}
      isLoading={loading}
      isClearable
      width={24}
    />
  );
}
