import { useEffect, useState } from "react";
import { api } from "./lib/api";
import { AddMonitorDialog } from "./components/AddMonitorDialog";
import { DetailPanel } from "./components/DetailPanel";
import { ExploratoryViews } from "./components/ExploratoryViews";
import { FilterToolbar } from "./components/FilterToolbar";
import { MonitorSidebar } from "./components/MonitorSidebar";
import { PackageGrid } from "./components/PackageGrid";
import {
  DEFAULT_FILTERS,
  type Filters,
  type PackageRow,
  type PackagesResponse,
} from "./types";

export function App() {
  const [monitorId, setMonitorId] = useState<number | null>(null);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [resp, setResp] = useState<PackagesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<PackageRow | null>(null);
  const [adding, setAdding] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const reload = () => setRefreshKey((k) => k + 1);

  useEffect(() => {
    const f: Filters = { ...filters, monitor_id: monitorId ?? undefined };
    setLoading(true);
    api
      .packages(f)
      .then((r) => {
        setResp(r);
        if (r.items.length && !r.items.some((p) => p.id === selected?.id)) {
          setSelected(null);
        }
      })
      .catch(() => setResp({ total: 0, page: 1, per_page: 50, items: [] }))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, monitorId, refreshKey]);

  useEffect(() => {
    const t = setInterval(reload, 20000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="layout">
      <div className="sidebar">
        <MonitorSidebar
          selectedId={monitorId}
          onSelect={setMonitorId}
          onAddClick={() => setAdding(true)}
          refreshKey={refreshKey}
        />
      </div>

      <div className="main">
        <FilterToolbar
          filters={filters}
          onChange={setFilters}
          total={resp?.total || 0}
        />

        <div className="content">
          <div className="grid-area">
            <PackageGrid
              items={resp?.items || []}
              loading={loading}
              selectedId={selected?.id ?? null}
              total={resp?.total || 0}
              page={filters.page}
              perPage={filters.per_page}
              onSelect={setSelected}
              onPage={(p) => setFilters({ ...filters, page: p })}
            />
            <ExploratoryViews refreshKey={refreshKey} />
          </div>

          <div className="detail-area">
            <DetailPanel pkg={selected} onReload={reload} />
          </div>
        </div>
      </div>

      {adding && (
        <AddMonitorDialog
          onClose={() => setAdding(false)}
          onCreated={reload}
        />
      )}
    </div>
  );
}
