import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../lib/api";
import { fmtBytes } from "../lib/format";
import { useMeta } from "../hooks/useMeta";
import type {
  HistogramBucket,
  LanguageCount,
  TimelinePoint,
} from "../types";

interface Props {
  refreshKey: number;
}

export function ExploratoryViews({ refreshKey }: Props) {
  const meta = useMeta();
  const [sizes, setSizes] = useState<HistogramBucket[]>([]);
  const [files, setFiles] = useState<HistogramBucket[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [languages, setLanguages] = useState<LanguageCount[]>([]);

  useEffect(() => {
    api.sizes().then(setSizes).catch(() => setSizes([]));
    api.files().then(setFiles).catch(() => setFiles([]));
    api.timeline(90).then(setTimeline).catch(() => setTimeline([]));
    api.languages(12).then(setLanguages).catch(() => setLanguages([]));
  }, [refreshKey]);

  const sizeData = sizes.map((b) => ({
    bucket: fmtBytes(b.lo),
    count: b.count,
  }));
  const fileData = files.map((b) => ({
    bucket: b.lo + "-" + (b.hi >= 100000 ? "∞" : b.hi),
    count: b.count,
  }));

  return (
    <div className="exploratory">
      <h3>Explore</h3>
      <div className="chart-row">
        <ChartCard title="Size distribution">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={sizeData}>
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: "#8b949e" }} />
              <YAxis tick={{ fontSize: 10, fill: "#8b949e" }} />
              <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d" }} />
              <Bar dataKey="count" fill="#58a6ff" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="File count distribution">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={fileData}>
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: "#8b949e" }} />
              <YAxis tick={{ fontSize: 10, fill: "#8b949e" }} />
              <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d" }} />
              <Bar dataKey="count" fill="#f0883e" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Publish timeline (last 90 days)">
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={timeline}>
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#8b949e" }} />
              <YAxis tick={{ fontSize: 10, fill: "#8b949e" }} />
              <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d" }} />
              <Line dataKey="count" stroke="#2ea043" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Top languages">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={languages} layout="vertical">
              <CartesianGrid stroke="#222" />
              <XAxis type="number" tick={{ fontSize: 10, fill: "#8b949e" }} />
              <YAxis
                dataKey="language"
                type="category"
                tick={{ fontSize: 10, fill: "#8b949e" }}
                width={80}
              />
              <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d" }} />
              <Bar dataKey="count">
                {languages.map((l) => (
                  <Cell
                    key={l.language}
                    fill={meta?.lang_colors[l.language] || "#58a6ff"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        background: "var(--panel-hi)",
        borderRadius: 6,
        padding: 10,
        border: "1px solid var(--border)",
      }}
    >
      <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>
        {title}
      </div>
      {children}
    </div>
  );
}
