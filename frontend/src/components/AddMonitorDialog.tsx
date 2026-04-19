import { useState } from "react";
import { api } from "../lib/api";
import { useMeta } from "../hooks/useMeta";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export function AddMonitorDialog({ onClose, onCreated }: Props) {
  const meta = useMeta();
  const [providers, setProviders] = useState<string[]>(["PyPI"]);
  const [query, setQuery] = useState("");
  const [interval, setInterval] = useState(300);
  const [mode, setMode] = useState<"pages" | "days">("pages");
  const [pages, setPages] = useState(1);
  const [days, setDays] = useState(3);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const allProviders = meta?.providers || [
    "PyPI", "npm", "GitHub", "DockerHub", "Libraries.io", "WebURL",
  ];

  const toggle = (p: string) => {
    setProviders((cur) =>
      cur.includes(p) ? cur.filter((x) => x !== p) : [...cur, p]
    );
  };

  const submit = async () => {
    if (!providers.length) {
      setErr("Pick at least one source");
      return;
    }
    if (!query.trim()) {
      setErr("Query is required");
      return;
    }
    setSaving(true);
    setErr("");
    try {
      await api.createMonitor({
        provider: providers[0],
        providers: providers.join("|"),
        query: query.trim(),
        interval_sec: interval,
        fetch_mode: mode,
        fetch_pages: pages,
        fetch_days: days,
      });
      onCreated();
      onClose();
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>New monitor</h2>

        <div className="form-row">
          <label>Sources</label>
          <div className="checkbox-grid">
            {allProviders.map((p) => (
              <label key={p}>
                <input
                  type="checkbox"
                  checked={providers.includes(p)}
                  onChange={() => toggle(p)}
                  style={{ flex: "0 0 auto" }}
                />
                <span
                  style={{
                    display: "inline-block",
                    width: 10,
                    height: 10,
                    borderRadius: 2,
                    background: meta?.provider_colors[p] || "#555",
                  }}
                />
                {p}
              </label>
            ))}
          </div>
        </div>

        <div className="form-row">
          <label>Query / URL</label>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              providers.includes("WebURL")
                ? "https://example.com/feed.xml"
                : "e.g. pandas"
            }
            autoFocus
          />
        </div>

        <div className="form-row">
          <label>Interval (sec)</label>
          <input
            className="num-input"
            type="number"
            min={10}
            value={interval}
            onChange={(e) => setInterval(parseInt(e.target.value || "0", 10))}
          />
        </div>

        <div className="form-row">
          <label>Fetch mode</label>
          <select value={mode} onChange={(e) => setMode(e.target.value as any)}>
            <option value="pages">By pages</option>
            <option value="days">By age (days)</option>
          </select>
        </div>

        {mode === "pages" ? (
          <div className="form-row">
            <label>Pages</label>
            <input
              className="num-input"
              type="number"
              min={1}
              value={pages}
              onChange={(e) => setPages(parseInt(e.target.value || "1", 10))}
            />
          </div>
        ) : (
          <div className="form-row">
            <label>Days back</label>
            <input
              className="num-input"
              type="number"
              min={1}
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value || "1", 10))}
            />
          </div>
        )}

        {err && (
          <div style={{ color: "var(--danger)", margin: "8px 0" }}>{err}</div>
        )}

        <div
          style={{
            display: "flex",
            gap: 8,
            justifyContent: "flex-end",
            marginTop: 12,
          }}
        >
          <button onClick={onClose}>Cancel</button>
          <button onClick={submit} disabled={saving}>
            {saving ? "Saving…" : "Create"}
          </button>
        </div>
      </div>
    </div>
  );
}
