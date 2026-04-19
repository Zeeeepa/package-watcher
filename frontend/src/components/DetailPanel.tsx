import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { fmtBytes, fmtNum, relTime } from "../lib/format";
import type { PackageDetail, PackageRow, PluginDef } from "../types";

interface Props {
  pkg: PackageRow | null;
  onReload: () => void;
}

export function DetailPanel({ pkg, onReload }: Props) {
  const [detail, setDetail] = useState<PackageDetail | null>(null);
  const [plugins, setPlugins] = useState<PluginDef[]>([]);
  const [tab, setTab] = useState<string>("overview");
  const [tabCache, setTabCache] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.plugins().then(setPlugins).catch(() => setPlugins([]));
  }, []);

  useEffect(() => {
    setMsg("");
    setTabCache({});
    setTab("overview");
    if (!pkg) {
      setDetail(null);
      return;
    }
    setLoading(true);
    api
      .package(pkg.id)
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [pkg?.id]);

  useEffect(() => {
    if (!pkg || tab === "overview") return;
    if (tabCache[tab]) return;
    setMsg("");
    api
      .runPlugin(pkg.id, tab, false)
      .then((r) => setTabCache((c) => ({ ...c, [tab]: r.result })))
      .catch((e) => setMsg(String(e)));
  }, [tab, pkg?.id]);

  if (!pkg) {
    return (
      <div className="empty">
        Select a package to see deep metadata, README, dependencies, file tree,
        analysis.
      </div>
    );
  }

  const p = detail?.package || pkg;

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
              setLoading(true);
              api
                .reindex(pkg.id)
                .then(() => {
                  onReload();
                  api.package(pkg.id).then(setDetail);
                  setTabCache({});
                })
                .finally(() => setLoading(false));
            }}
          >
            Re-index
          </button>
          <button
            onClick={() => {
              setMsg("Downloading…");
              api
                .downloadPackage(pkg.id)
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
        {plugins.map((pl) => (
          <div
            key={pl.id}
            className={"tab" + (tab === pl.id ? " active" : "")}
            onClick={() => setTab(pl.id)}
          >
            {pl.label}
          </div>
        ))}
      </div>

      <div className="detail-tab-content">
        {tab === "overview" &&
          (loading ? (
            <em>Loading…</em>
          ) : (
            <Overview detail={detail} />
          ))}
        {tab !== "overview" && !tabCache[tab] && <em>Computing…</em>}
        {tab !== "overview" && tabCache[tab] && tabCache[tab]}
      </div>
    </div>
  );
}

function Overview({ detail }: { detail: PackageDetail | null }) {
  if (!detail) return <em>Loading…</em>;
  const m = detail.metadata || {};
  const p = detail.package || {};
  const rows: [string, string | number | null][] = [
    ["Description", p.description],
    ["License", m.license_spdx || ""],
    ["Homepage", m.homepage || ""],
    ["Stars", m.stars || null],
    ["Forks", m.forks || null],
    ["Open issues", m.open_issues || null],
    ["Compliance", m.compliance_score ? `${m.compliance_score}/100` : null],
    ["Indexed", m.indexed_at ? relTime(m.indexed_at as string) : null],
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
