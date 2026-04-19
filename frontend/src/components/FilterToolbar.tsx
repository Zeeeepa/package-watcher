import type { Filters } from "../types";
import { useMeta } from "../hooks/useMeta";

interface Props {
  filters: Filters;
  onChange: (next: Filters) => void;
  total: number;
}

const SORTS: [string, string][] = [
  ["published_at", "Published"],
  ["fetched_at", "Fetched"],
  ["size_bytes", "Size"],
  ["file_count", "File count"],
  ["name", "Name"],
  ["provider", "Provider"],
];

export function FilterToolbar({ filters, onChange, total }: Props) {
  const meta = useMeta();
  const upd = (patch: Partial<Filters>) =>
    onChange({ ...filters, ...patch, page: 1 });

  const toggleProv = (p: string) => {
    const has = filters.providers.includes(p);
    upd({
      providers: has
        ? filters.providers.filter((x) => x !== p)
        : [...filters.providers, p],
    });
  };

  return (
    <div className="toolbar">
      <input
        placeholder="Search…"
        value={filters.search}
        onChange={(e) => upd({ search: e.target.value })}
        style={{ minWidth: 220 }}
      />

      <span style={{ color: "var(--muted)", fontSize: 11 }}>Providers:</span>
      {(meta?.providers || []).map((p) => {
        const on = filters.providers.includes(p);
        return (
          <button
            key={p}
            onClick={() => toggleProv(p)}
            style={{
              padding: "4px 8px",
              borderColor: on ? meta?.provider_colors[p] : "var(--border)",
              background: on ? meta?.provider_colors[p] : "var(--panel-hi)",
              color: on ? "#fff" : "var(--text)",
              fontSize: 11,
            }}
          >
            {p}
          </button>
        );
      })}

      <span style={{ color: "var(--muted)", fontSize: 11, marginLeft: 10 }}>
        Size (bytes):
      </span>
      <input
        type="number"
        className="num-input"
        placeholder="min"
        value={filters.min_size ?? ""}
        onChange={(e) =>
          upd({ min_size: e.target.value ? +e.target.value : undefined })
        }
      />
      <input
        type="number"
        className="num-input"
        placeholder="max"
        value={filters.max_size ?? ""}
        onChange={(e) =>
          upd({ max_size: e.target.value ? +e.target.value : undefined })
        }
      />

      <span style={{ color: "var(--muted)", fontSize: 11 }}>Files:</span>
      <input
        type="number"
        className="num-input"
        placeholder="min"
        value={filters.min_files ?? ""}
        onChange={(e) =>
          upd({ min_files: e.target.value ? +e.target.value : undefined })
        }
      />
      <input
        type="number"
        className="num-input"
        placeholder="max"
        value={filters.max_files ?? ""}
        onChange={(e) =>
          upd({ max_files: e.target.value ? +e.target.value : undefined })
        }
      />

      <span style={{ color: "var(--muted)", fontSize: 11 }}>Published:</span>
      <input
        type="date"
        value={(filters.published_after || "").slice(0, 10)}
        onChange={(e) => upd({ published_after: e.target.value || undefined })}
      />
      <input
        type="date"
        value={(filters.published_before || "").slice(0, 10)}
        onChange={(e) => upd({ published_before: e.target.value || undefined })}
      />

      <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <input
          type="checkbox"
          checked={filters.new_only}
          onChange={(e) => upd({ new_only: e.target.checked })}
        />
        New
      </label>

      <span style={{ flex: 1 }} />

      <span style={{ color: "var(--muted)", fontSize: 11 }}>Sort:</span>
      <select
        value={filters.sort_col}
        onChange={(e) => upd({ sort_col: e.target.value })}
      >
        {SORTS.map(([v, label]) => (
          <option key={v} value={v}>
            {label}
          </option>
        ))}
      </select>
      <button
        onClick={() => upd({ sort_asc: !filters.sort_asc })}
        title={filters.sort_asc ? "Ascending" : "Descending"}
      >
        {filters.sort_asc ? "↑" : "↓"}
      </button>

      <span className="stat-pill">{total.toLocaleString()} results</span>
    </div>
  );
}
