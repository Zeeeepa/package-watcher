export function fmtBytes(n: number | null | undefined): string {
  if (n == null || isNaN(n) || n <= 0) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1 << 20) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1 << 30) return `${(n / (1 << 20)).toFixed(1)} MB`;
  return `${(n / (1 << 30)).toFixed(1)} GB`;
}

export function relTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = Date.parse(iso);
  if (isNaN(d)) return iso.slice(0, 10);
  const sec = Math.floor((Date.now() - d) / 1000);
  if (sec < 60) return "just now";
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
  if (sec < 2_592_000) return `${Math.floor(sec / 86400)}d ago`;
  if (sec < 31_536_000) return `${Math.floor(sec / 2_592_000)}mo ago`;
  return `${Math.floor(sec / 31_536_000)}y ago`;
}

export function fmtNum(n: number | null | undefined): string {
  if (n == null) return "—";
  return n.toLocaleString();
}
