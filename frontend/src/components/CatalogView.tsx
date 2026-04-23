import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { fmtBytes, fmtNum, relTime } from "../lib/format";
import type { CatalogRow } from "../types";

type SortKey =
  | "name"
  | "provider"
  | "language"
  | "size_bytes"
  | "file_count"
  | "stars"
  | "compliance_score"
  | "published_at"
  | "fetched_at";

interface Props {
  refreshKey: number;
  onSelect: (id: number) => void;
}

export function CatalogView({ refreshKey, onSelect }: Props) {
  const [rows, setRows] = useState<CatalogRow[]>([]);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("fetched_at");
  const [sortDesc, setSortDesc] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api
      .catalog(1000, 0, search)
      .then((r) => setRows(r.items))
      .finally(() => setLoading(false));
  }, [refreshKey, search]);

  const sorted = [...rows].sort((a, b) => {
    const av = (a as any)[sortKey];
    const bv = (b as any)[sortKey];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    const cmp = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv));
    return sortDesc ? -cmp : cmp;
  });

  const setSort = (k: SortKey) => {
    if (k === sortKey) setSortDesc(!sortDesc);
    else {
      setSortKey(k);
      setSortDesc(true);
    }
  };

  const th = (k: SortKey, label: string) => (
    <th
      onClick={() => setSort(k)}
      style={{ cursor: "pointer", userSelect: "none", whiteSpace: "nowrap" }}
      title="Click to sort"
    >
      {label} {sortKey === k ? (sortDesc ? "↓" : "↑") : ""}
    </th>
  );

  return (
    <div className="catalog-view">
      <div className="catalog-toolbar">
        <input
          placeholder="Search catalog…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span style={{ color: "var(--muted)", fontSize: 12 }}>
          {loading ? "Loading…" : `${sorted.length} shown`}
        </span>
      </div>
      <div className="catalog-scroll">
        <table className="catalog-table">
          <thead>
            <tr>
              {th("name", "Name")}
              {th("provider", "Src")}
              {th("language", "Lang")}
              {th("size_bytes", "Size")}
              {th("file_count", "Files")}
              {th("stars", "★")}
              {th("compliance_score", "Score")}
              <th>License</th>
              {th("published_at", "Published")}
              {th("fetched_at", "Fetched")}
              <th>Indexed</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr
                key={r.id}
                onClick={() => onSelect(r.id)}
                style={{ cursor: "pointer" }}
              >
                <td>
                  <div style={{ fontWeight: 600 }}>{r.name}</div>
                  <div
                    style={{
                      color: "var(--muted)",
                      fontSize: 11,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                      maxWidth: 460,
                    }}
                  >
                    {r.description || ""}
                  </div>
                </td>
                <td>{r.provider}</td>
                <td>{r.language || "—"}</td>
                <td>{fmtBytes(r.size_bytes)}</td>
                <td>{fmtNum(r.file_count)}</td>
                <td>{fmtNum(r.stars)}</td>
                <td>
                  <ComplianceBadge score={r.compliance_score} />
                </td>
                <td>{r.license_spdx || "—"}</td>
                <td>{relTime(r.published_at)}</td>
                <td>{relTime(r.fetched_at)}</td>
                <td>{relTime(r.last_full_indexed_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ComplianceBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? "#238636" : score >= 50 ? "#9e6a03" : score > 0 ? "#b62324" : "#444";
  return (
    <span
      style={{
        background: color,
        color: "white",
        padding: "1px 6px",
        borderRadius: 4,
        fontSize: 11,
        fontWeight: 600,
      }}
    >
      {score}
    </span>
  );
}
