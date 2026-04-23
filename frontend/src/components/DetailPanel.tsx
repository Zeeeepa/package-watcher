import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { fmtBytes, fmtNum, relTime } from "../lib/format";
import type { PackageFull, PackageRow, PluginDef } from "../types";

interface Props {
  pkg: PackageRow | null;
  pkgId?: number | null;
  onReload: () => void;
}

export function DetailPanel({ pkg, pkgId, onReload }: Props) {
  const activeId = pkg?.id ?? pkgId ?? null;
  const [full, setFull] = useState<PackageFull | null>(null);
  const [plugins, setPlugins] = useState<PluginDef[]>([]);
  const [tab, setTab] = useState<string>("overview");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.plugins().then(setPlugins).catch(() => setPlugins([]));
  }, []);

  useEffect(() => {
    setMsg("");
    setTab("overview");
    if (activeId == null) {
      setFull(null);
      return;
    }
    setLoading(true);
    api
      .packageFull(activeId)
      .then(setFull)
      .catch(() => setFull(null))
      .finally(() => setLoading(false));
  }, [activeId]);

  const refreshFull = () => {
    if (activeId == null) return;
    api.packageFull(activeId).then(setFull).catch(() => {});
  };

  if (activeId == null) {
    return (
      <div className="empty">
        Select a package to see deep metadata, README, dependencies, file tree,
        analysis — all stored in the DB.
      </div>
    );
  }

  const p = full?.package || pkg || {};
  const analyses = full?.analyses || {};

  const onRunPlugin = async (pluginId: string) => {
    if (activeId == null) return;
    setMsg(`Running ${pluginId}…`);
    try {
      await api.runPlugin(activeId, pluginId, true);
      refreshFull();
      setMsg("");
    } catch (e) {
      setMsg(String(e));
    }
  };

  return (
    <div>
      <div style={{ padding: 14, borderBottom: "1px solid var(--border)" }}>
        <h2 style={{ margin: "0 0 4px", fontSize: 15, wordBreak: "break-all" }}>
          {p.name}
        </h2>
        <div style={{ fontSize: 12, color: "var(--muted)" }}>
          {p.provider} · v{p.version || "?"} · {p.author || "—"}
        </div>
        <div
          style={{
            display: "flex",
            gap: 10,
            flexWrap: "wrap",
            fontSize: 11,
            marginTop: 6,
            color: "var(--muted)",
          }}
        >
          <span>📦 {fmtBytes(p.size_bytes)}</span>
          <span>📄 {fmtNum(p.file_count)}</span>
          <span>⏱ {relTime(p.published_at)}</span>
          {p.url && (
            <a href={p.url} target="_blank" rel="noreferrer">
              ↗ open
            </a>
          )}
        </div>
        <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
          <button
            onClick={() => {
              if (activeId == null) return;
              setLoading(true);
              setMsg("Re-indexing (running all plugins)…");
              api
                .reindex(activeId)
                .then(() => {
                  onReload();
                  refreshFull();
                  setMsg("Re-indexed.");
                })
                .catch((e) => setMsg(String(e)))
                .finally(() => setLoading(false));
            }}
          >
            Re-index
          </button>
          <button
            onClick={() => {
              if (activeId == null) return;
              setMsg("Downloading…");
              api
                .downloadPackage(activeId)
                .then((r) => setMsg(r.message))
                .catch((e) => setMsg(String(e)))
                .finally(onReload);
            }}
          >
            Download
          </button>
          {msg && (
            <span style={{ fontSize: 11, color: "var(--muted)" }}>{msg}</span>
          )}
        </div>
      </div>

      <div className="tab-bar">
        <div
          className={"tab" + (tab === "overview" ? " active" : "")}
          onClick={() => setTab("overview")}
        >
          Overview
        </div>
        <div
          className={"tab" + (tab === "raw" ? " active" : "")}
          onClick={() => setTab("raw")}
        >
          Raw
        </div>
        {plugins.map((pl) => (
          <div
            key={pl.id}
            className={
              "tab" +
              (tab === pl.id ? " active" : "") +
              (analyses[pl.id] ? " has-data" : "")
            }
            onClick={() => setTab(pl.id)}
            title={analyses[pl.id] ? "Cached in DB" : "Not yet indexed"}
          >
            {pl.label}
            {analyses[pl.id] ? " ●" : ""}
          </div>
        ))}
      </div>

      <div className="detail-tab-content">
        {tab === "overview" && (loading ? <em>Loading…</em> : <Overview full={full} />)}
        {tab === "raw" && <RawView full={full} />}
        {tab !== "overview" && tab !== "raw" && (
          <PluginPane
            pluginId={tab}
            analyses={analyses}
            onRun={() => onRunPlugin(tab)}
          />
        )}
      </div>
    </div>
  );
}

function Overview({ full }: { full: PackageFull | null }) {
  if (!full) return <em>Loading…</em>;
  const m = full.metadata || {};
  const p = full.package || {};
  const rows: [string, string | number | null][] = [
    ["Description", p.description],
    ["License", m.license_spdx || ""],
    ["Homepage", m.homepage || ""],
    ["Stars", m.stars || null],
    ["Forks", m.forks || null],
    ["Open issues", m.open_issues || null],
    ["Compliance", m.compliance_score ? `${m.compliance_score}/100` : null],
    ["Last indexed", m.last_full_indexed_at ? relTime(m.last_full_indexed_at as string) : null],
  ];
  return (
    <>
      {rows
        .filter(([, v]) => v !== null && v !== "" && v !== undefined)
        .map(([k, v]) => (
          <div
            key={k}
            style={{ display: "flex", gap: 8, marginBottom: 4, fontSize: 12 }}
          >
            <span style={{ color: "var(--muted)", width: 100 }}>{k}</span>
            <span style={{ flex: 1, wordBreak: "break-all" }}>{String(v)}</span>
          </div>
        ))}
      {(m.topics_json || []).length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div style={{ color: "var(--muted)", fontSize: 12, marginBottom: 4 }}>
            Topics
          </div>
          <div className="badges">
            {(m.topics_json as string[]).map((t) => (
              <span key={t} className="badge">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function RawView({ full }: { full: PackageFull | null }) {
  if (!full) return <em>Loading…</em>;
  const raw = full.package?.raw_json;
  if (!raw) return <em>No raw payload stored.</em>;
  return (
    <pre
      style={{
        fontSize: 11,
        background: "var(--bg)",
        padding: 8,
        borderRadius: 4,
        maxHeight: 520,
        overflow: "auto",
      }}
    >
      {JSON.stringify(raw, null, 2)}
    </pre>
  );
}

function PluginPane({
  pluginId,
  analyses,
  onRun,
}: {
  pluginId: string;
  analyses: Record<string, { result: string; created_at: string }>;
  onRun: () => void;
}) {
  const entry = analyses[pluginId];
  if (!entry) {
    return (
      <div>
        <em>No cached result in DB.</em>{" "}
        <button onClick={onRun}>Run plugin</button>
      </div>
    );
  }
  return (
    <div>
      <div style={{ fontSize: 10, color: "var(--muted)", marginBottom: 6 }}>
        Cached {relTime(entry.created_at)} ·{" "}
        <button onClick={onRun} style={{ fontSize: 10 }}>
          Re-run
        </button>
      </div>
      <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, margin: 0 }}>
        {entry.result}
      </pre>
    </div>
  );
}
