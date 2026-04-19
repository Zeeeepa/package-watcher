import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { relTime } from "../lib/format";
import type { Monitor } from "../types";

interface Props {
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  onAddClick: () => void;
  refreshKey: number;
}

export function MonitorSidebar({
  selectedId,
  onSelect,
  onAddClick,
  refreshKey,
}: Props) {
  const [items, setItems] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(false);

  const reload = () => {
    setLoading(true);
    api.monitors()
      .then(setItems)
      .finally(() => setLoading(false));
  };

  useEffect(reload, [refreshKey]);

  useEffect(() => {
    const t = setInterval(reload, 15000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 10,
        }}
      >
        <h3 style={{ margin: 0, fontSize: 13, color: "var(--muted)" }}>
          Monitors
        </h3>
        <div style={{ display: "flex", gap: 4 }}>
          <button onClick={onAddClick} title="Add monitor">+</button>
          <button onClick={() => onSelect(null)} title="Show all packages">
            All
          </button>
        </div>
      </div>

      {items.length === 0 && !loading && (
        <div className="empty" style={{ fontSize: 12 }}>
          No monitors yet. Click <strong>+</strong> to add one.
        </div>
      )}

      {items.map((m) => (
        <div
          key={m.id}
          className={"monitor-item" + (m.id === selectedId ? " active" : "")}
          onClick={() => onSelect(m.id)}
        >
          <h4>
            <span>
              <span
                className="dot"
                style={{ background: m.enabled ? "var(--ok)" : "var(--muted)" }}
              />
              {m.query || "(empty)"}
            </span>
            <span style={{ display: "flex", gap: 4 }}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  api.triggerMonitor(m.id).then(() => setTimeout(reload, 800));
                }}
                title="Fetch now"
                style={{ padding: "2px 6px", fontSize: 11 }}
              >
                ↻
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  api
                    .enableMonitor(m.id, !m.enabled)
                    .then(reload);
                }}
                title={m.enabled ? "Pause" : "Start"}
                style={{ padding: "2px 6px", fontSize: 11 }}
              >
                {m.enabled ? "⏸" : "▶"}
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm(`Delete monitor "${m.query}"?`)) {
                    api.deleteMonitor(m.id).then(() => {
                      if (selectedId === m.id) onSelect(null);
                      reload();
                    });
                  }
                }}
                title="Delete"
                style={{ padding: "2px 6px", fontSize: 11 }}
              >
                ✕
              </button>
            </span>
          </h4>
          <small>
            {m.providers || m.provider} · every {m.interval_sec}s ·
            {" "}
            {m.fetch_mode === "pages" ? `${m.fetch_pages}p` : `${m.fetch_days}d`}
          </small>
          <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>
            {m.total_saved} saved · last: {relTime(m.last_ts)} (+{m.last_new})
          </div>
        </div>
      ))}
    </div>
  );
}
