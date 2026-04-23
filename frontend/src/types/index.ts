export interface Monitor {
  id: number;
  provider: string;
  providers: string | null;
  query: string;
  enabled: number;
  interval_sec: number;
  fetch_mode: string;
  fetch_pages: number;
  fetch_days: number;
  last_ts: string | null;
  last_new: number;
  total_saved: number;
  created_at: string;
}

export interface PackageRow {
  id: number;
  provider: string;
  name: string;
  description: string | null;
  version: string | null;
  author: string | null;
  published_at: string | null;
  fetched_at: string | null;
  size_bytes: number | null;
  file_count: number | null;
  language: string | null;
  download_status: string | null;
  url: string | null;
  sources: string[];
  compliance_score: number;
  stars: number;
  is_new: number;
}

export interface PackagesResponse {
  total: number;
  page: number;
  per_page: number;
  items: PackageRow[];
}

export interface PackageDetail {
  package: Record<string, any>;
  metadata: Record<string, any>;
}

export interface PackageFull extends PackageDetail {
  analyses: Record<string, { result: string; created_at: string }>;
}

export interface CatalogRow {
  id: number;
  provider: string;
  name: string;
  description: string | null;
  version: string | null;
  language: string | null;
  published_at: string | null;
  fetched_at: string | null;
  size_bytes: number | null;
  file_count: number | null;
  url: string | null;
  download_status: string | null;
  stars: number;
  forks: number;
  compliance_score: number;
  license_spdx: string | null;
  homepage: string | null;
  last_full_indexed_at: string | null;
}

export interface TopRow {
  id: number;
  provider: string;
  name: string;
  language: string | null;
  version: string | null;
  stars: number;
  score: number;
}

export interface DashboardStats {
  total: number;
  by_provider: Record<string, number>;
  monitors: number;
  active_monitors: number;
  downloaded: number;
  avg_compliance: number;
}

export interface MetaResponse {
  providers: string[];
  provider_colors: Record<string, string>;
  lang_colors: Record<string, string>;
}

export interface PluginDef {
  id: string;
  label: string;
  cache: boolean;
}

export interface HistogramBucket {
  lo: number;
  hi: number;
  count: number;
}

export interface TimelinePoint {
  date: string;
  count: number;
}

export interface LanguageCount {
  language: string;
  count: number;
}

export interface Filters {
  providers: string[];
  languages: string[];
  search: string;
  min_size?: number;
  max_size?: number;
  min_files?: number;
  max_files?: number;
  published_after?: string;
  published_before?: string;
  new_only: boolean;
  dl_only: boolean;
  monitor_id?: number;
  sort_col: string;
  sort_asc: boolean;
  page: number;
  per_page: number;
}

export const DEFAULT_FILTERS: Filters = {
  providers: [],
  languages: [],
  search: "",
  new_only: false,
  dl_only: false,
  sort_col: "published_at",
  sort_asc: false,
  page: 1,
  per_page: 50,
};
