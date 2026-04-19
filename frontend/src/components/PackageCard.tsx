import type { PackageRow } from "../types";
import { fmtBytes, fmtNum, relTime } from "../lib/format";
import { useMeta } from "../hooks/useMeta";

interface Props {
  pkg: PackageRow;
  selected: boolean;
  onClick: () => void;
}

export function PackageCard({ pkg, selected, onClick }: Props) {
  const meta = useMeta();
  const provColor = meta?.provider_colors[pkg.provider] || "#555";
  const langColor = meta?.lang_colors[pkg.language || ""] || "#555";
  return (
    <div
      className={"pkg-card" + (selected ? " selected" : "")}
      onClick={onClick}
    >
      <h3>
        <span className="provider-color" style={{ background: provColor }} />
        {pkg.name}
        {pkg.is_new ? (
          <span
            className="badge"
            style={{ background: "var(--ok)", color: "#fff", marginLeft: 4 }}
          >
            NEW
          </span>
        ) : null}
      </h3>
      <p>{pkg.description || <em>(no description)</em>}</p>
      <div className="badges">
        <span className="badge" style={{ background: provColor, color: "#fff" }}>
          {pkg.provider}
        </span>
        {pkg.language && (
          <span
            className="badge"
            style={{ borderColor: langColor, color: langColor }}
          >
            {pkg.language}
          </span>
        )}
        {pkg.version && <span className="badge">v{pkg.version}</span>}
        {pkg.download_status === "done" && (
          <span className="badge" style={{ background: "var(--ok)", color: "#fff" }}>
            ↓ downloaded
          </span>
        )}
        {pkg.compliance_score > 0 && (
          <span
            className="badge"
            style={{
              background:
                pkg.compliance_score >= 90
                  ? "var(--ok)"
                  : pkg.compliance_score >= 60
                    ? "var(--warn)"
                    : "var(--danger)",
              color: "#fff",
            }}
          >
            {pkg.compliance_score}/100
          </span>
        )}
      </div>
      <div className="meta-row">
        <span>📦 {fmtBytes(pkg.size_bytes)}</span>
        <span>📄 {fmtNum(pkg.file_count)}</span>
        <span>⏱ {relTime(pkg.published_at)}</span>
        {pkg.stars ? <span>★ {fmtNum(pkg.stars)}</span> : null}
      </div>
    </div>
  );
}
