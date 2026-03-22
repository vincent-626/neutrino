import { getBackendSrv } from '@grafana/runtime';
import { PLUGIN_ID } from './constants';
import type { LabelsResponse, SearchRequest, SearchResponse } from './types';

const BASE = `/api/plugins/${PLUGIN_ID}/resources`;

export async function search(req: SearchRequest): Promise<SearchResponse> {
  return getBackendSrv()
    .post<SearchResponse>(`${BASE}/search`, req)
    .toPromise();
}

export async function getLabelValues(labelName: string): Promise<string[]> {
  const resp = await getBackendSrv()
    .get<LabelsResponse>(`${BASE}/labels`, { name: labelName })
    .toPromise();
  return resp.values;
}
