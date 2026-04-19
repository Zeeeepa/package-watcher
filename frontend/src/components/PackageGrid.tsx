import type { PackageRow } from "../types";
import { PackageCard } from "./PackageCard";

interface Props {
  items: PackageRow[];
  loading: boolean;
  selectedId: number | null;
  onSelect: (p: PackageRow) => void;
  total: number;
  page: number;
  perPage: number;
  onPage: (p: number) => void;
}

export function PackageGrid({
  items,
  loading,
  selectedId,
  onSelect,
  total,
  page,
  perPage,
  onPage,
}: Props) {
  if (loading && !items.length) {
    return <div className="loading">Loading packages…</div>;
  }
  if (!loading && !items.length) {
    return (
      <div className="empty">
        No packages match these filters. Trigger a monitor or broaden the
        filters.
      </div>
    );
  }
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  return (
    <>
      <div className="card-grid">
        {items.map((p) => (
          <PackageCard
            key={p.id}
            pkg={p}
            selected={p.id === selectedId}
            onClick={() => onSelect(p)}
          />
        ))}
      </div>
      <div className="pagination">
        <button disabled={page <= 1} onClick={() => onPage(1)}>
          «
        </button>
        <button disabled={page <= 1} onClick={() => onPage(page - 1)}>
          ‹
        </button>
        <span style={{ color: "var(--muted)" }}>
          page {page} / {totalPages}
        </span>
        <button disabled={page >= totalPages} onClick={() => onPage(page + 1)}>
          ›
        </button>
        <button disabled={page >= totalPages} onClick={() => onPage(totalPages)}>
          »
        </button>
      </div>
    </>
  );
}
