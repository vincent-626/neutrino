export interface SearchRequest {
  query: string;
  service?: string;
  severity?: string;
  start_ns: number;
  end_ns: number;
  top_k?: number;
}

export interface LogResult {
  score: number;
  timestamp_ns: number;
  labels: Record<string, string>;
  line: string;
}

export interface SearchResponse {
  results: LogResult[];
  total_fetched: number;
  truncated: boolean;
}

export interface LabelsResponse {
  values: string[];
}
