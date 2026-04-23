import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { fmtNum } from "../lib/format";
import type { DashboardStats, TopRow } from "../types";

interface Props {
  refreshKey: number;
  onSelect: (id: number) => void;
}

export function AnalyzerView({ refreshKey, onSelect }: Props) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [starred, setStarred] = useState<TopRow[]>([]);
  const [compliant, setCompliant] = useState<TopRow[]>([]);

  useEffect(() => {
    Promise.all([
      api.stats().then(setStats).catch(() => setStats(null)),
      api.topStarred(30).then(setStarred).catch(() => setStarred([])),
      api.topCompliance(30).then(setCompliant).catch(() => setCompliant([])),
    ]);
  }, [refreshKey]);

  return (
    <div className="analyzer-view">
      <div className="analyzer-grid">
        <Stat label="Total packages" value={fmtNum(stats?.total)} />
        <Stat label="Downloaded" value={fmtNum(stats?.downloaded)} />
        <Stat label="Monitors" value={`${stats?.active_monitors ?? 0}/${stats?.monitors ?? 0}`} />
        <Stat label="Avg compliance" value={stats?.avg_compliance?.toFixed(1) ?? "—"} />
      </div>

      <div className="analyzer-columns">
        <TopPanel title="★ Most starred" rows={starred} metric="stars" onSelect={onSelect} />
        <TopPanel title="✓ Highest compliance" rows={compliant} metric="score" onSelect={onSelect} />
      </div>

      {stats && (
        <div className="by-provider">
          <h3>By provider</h3>
          <div className="provider-list">
            {Object.entries(stats.by_provider).map(([prov, n]) => (
              <div key={prov} className="provider-row">
                <span className="provider-name">{prov}</span>
                <span className="provider-count">{fmtNum(n)}</span>
                <div
                  className="provider-bar"
                  style={{
                    width: `${Math.min(100, (n / stats.total) * 100)}%`,
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function TopPanel({
  title,
  rows,
  metric,
  onSelect,
}: {
  title: string;
  rows: TopRow[];
  metric: "stars" | "score";
  onSelect: (id: number) => void;
}) {
  return (
    <div className="top-panel">
      <h3>{title}</h3>
      {rows.length === 0 && <em>No data yet. Trigger a monitor to index packages.</em>}
      <div className="top-list">
        {rows.map((r) => (
          <div key={r.id} className="top-row" onClick={() => onSelect(r.id)}>
            <span className="top-rank">{metric === "stars" ? r.stars : r.score}</span>
            <span className="top-name">
              <strong>{r.name}</strong>{" "}
              <span style={{ color: "var(--muted)" }}>
                {r.provider} · {r.language || "—"}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
