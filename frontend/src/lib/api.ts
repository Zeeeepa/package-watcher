import type {
  CatalogRow,
  DashboardStats,
  HistogramBucket,
  LanguageCount,
  MetaResponse,
  Monitor,
  PackageDetail,
  PackageFull,
  PackagesResponse,
  Filters,
  PluginDef,
  TimelinePoint,
  TopRow,
} from "../types";

const BASE = "/api";

async function j<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`${r.status} ${r.statusText} — ${txt}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  meta: () => j<MetaResponse>(`${BASE}/stats/meta`),
  stats: () => j<DashboardStats>(`${BASE}/stats`),

  sizes: () => j<HistogramBucket[]>(`${BASE}/stats/histogram/sizes`),
  files: () => j<HistogramBucket[]>(`${BASE}/stats/histogram/files`),
  timeline: (days = 90) =>
    j<TimelinePoint[]>(`${BASE}/stats/timeline?days=${days}`),
  languages: (limit = 20) =>
    j<LanguageCount[]>(`${BASE}/stats/languages?limit=${limit}`),

  monitors: () => j<Monitor[]>(`${BASE}/monitors`),
  createMonitor: (body: Partial<Monitor> & { provider: string; query: string }) =>
    j<Monitor>(`${BASE}/monitors`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateMonitor: (id: number, body: Partial<Monitor>) =>
    j<Monitor>(`${BASE}/monitors/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteMonitor: (id: number) =>
    j<{ ok: boolean }>(`${BASE}/monitors/${id}`, { method: "DELETE" }),
  triggerMonitor: (id: number) =>
    j<{ ok: boolean }>(`${BASE}/monitors/${id}/trigger`, { method: "POST" }),
  enableMonitor: (id: number, enabled: boolean) =>
    j<Monitor>(`${BASE}/monitors/${id}/enable`, {
      method: "POST",
      body: JSON.stringify({ enabled }),
    }),

  packages: (filters: Filters) => {
    const qs = new URLSearchParams();
    qs.set("page", String(filters.page));
    qs.set("per_page", String(filters.per_page));
    qs.set("sort_col", filters.sort_col);
    qs.set("sort_asc", String(filters.sort_asc));
    if (filters.providers.length)
      qs.set("providers", filters.providers.join(","));
    if (filters.languages.length)
      qs.set("languages", filters.languages.join(","));
    if (filters.search) qs.set("search", filters.search);
    if (filters.min_size != null) qs.set("min_size", String(filters.min_size));
    if (filters.max_size != null) qs.set("max_size", String(filters.max_size));
    if (filters.min_files != null)
      qs.set("min_files", String(filters.min_files));
    if (filters.max_files != null)
      qs.set("max_files", String(filters.max_files));
    if (filters.published_after)
      qs.set("published_after", filters.published_after);
    if (filters.published_before)
      qs.set("published_before", filters.published_before);
    if (filters.new_only) qs.set("new_only", "true");
    if (filters.dl_only) qs.set("dl_only", "true");
    if (filters.monitor_id != null)
      qs.set("monitor_id", String(filters.monitor_id));
    return j<PackagesResponse>(`${BASE}/packages?${qs.toString()}`);
  },
  package: (id: number) => j<PackageDetail>(`${BASE}/packages/${id}`),
  packageFull: (id: number) => j<PackageFull>(`${BASE}/packages/${id}/full`),
  packageLive: (id: number) =>
    j<{ package: any; live: any }>(`${BASE}/packages/${id}/live`),
  downloadPackage: (id: number) =>
    j<{ ok: boolean; message: string }>(`${BASE}/packages/${id}/download`, {
      method: "POST",
    }),
  deletePackages: (ids: number[]) =>
    j<{ deleted: number }>(`${BASE}/packages/delete`, {
      method: "POST",
      body: JSON.stringify({ ids }),
    }),

  plugins: () => j<PluginDef[]>(`${BASE}/analysis/plugins`),
  runPlugin: (pkgId: number, pluginId: string, force = false) =>
    j<{ cached: boolean; result: string }>(
      `${BASE}/analysis/${pkgId}/${pluginId}${force ? "?force=true" : ""}`
    ),
  reindex: (pkgId: number) =>
    j<{ compliance: any }>(`${BASE}/analysis/${pkgId}/reindex`, {
      method: "POST",
    }),

  detectFeed: (url: string) =>
    j<{ type: string; feed_url: string; sample: string[]; count: number }>(
      `${BASE}/feeds/detect?url=${encodeURIComponent(url)}`
    ),

  topStarred: (limit = 20) =>
    j<TopRow[]>(`${BASE}/stats/top_starred?limit=${limit}`),
  topCompliance: (limit = 20) =>
    j<TopRow[]>(`${BASE}/stats/top_compliance?limit=${limit}`),
  catalog: (limit = 500, offset = 0, search = "") => {
    const qs = new URLSearchParams();
    qs.set("limit", String(limit));
    qs.set("offset", String(offset));
    if (search) qs.set("search", search);
    return j<{ items: CatalogRow[]; offset: number; limit: number }>(
      `${BASE}/stats/catalog?${qs.toString()}`
    );
  },
};
