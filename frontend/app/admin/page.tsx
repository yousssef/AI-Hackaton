"use client";

import { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://ai-hackaton-06yr.onrender.com";

// ——— Static mock data (mirrors data.js, used where real API has no endpoint) ———
const SWB_FUNNEL = [
  { stage: "Ingested",     count: 10388, pct: 100 },
  { stage: "Deduplicated", count: 8721,  pct: 84.0 },
  { stage: "Rule-passed",  count: 6228,  pct: 60.0 },
  { stage: "LLM-verified", count: 4912,  pct: 47.3 },
  { stage: "Ranked",       count: 1840,  pct: 17.7 },
  { stage: "Surfaced",     count: 312,   pct: 3.0 },
];

const SWB_TRUST_HIST = [
  { bucket: "0-9",   count: 142 },
  { bucket: "10-19", count: 178 },
  { bucket: "20-29", count: 224 },
  { bucket: "30-39", count: 268 },
  { bucket: "40-49", count: 312 },
  { bucket: "50-59", count: 401 },
  { bucket: "60-69", count: 612 },
  { bucket: "70-79", count: 894 },
  { bucket: "80-89", count: 1124 },
  { bucket: "90-100", count: 757 },
];

const SWB_VERIFIED_TIMESERIES = [
  86.1, 84.4, 87.2, 88.0, 85.7, 86.3, 87.9, 88.4, 87.1, 89.0, 88.5, 89.3, 88.7, 89.1,
];

const SWB_SOURCES = [
  { id: "greenhouse", name: "Greenhouse",       tier: 1, status: "healthy",  pulled_24h: 4821, kept: 2914, kept_pct: 60, last_run: "3m ago",  avg_latency_ms: 420,  error_rate: 0.001 },
  { id: "lever",      name: "Lever",            tier: 1, status: "healthy",  pulled_24h: 2103, kept: 1289, kept_pct: 61, last_run: "3m ago",  avg_latency_ms: 380,  error_rate: 0.002 },
  { id: "remoteok",   name: "RemoteOK",         tier: 2, status: "degraded", pulled_24h: 814,  kept: 412,  kept_pct: 51, last_run: "14m ago", avg_latency_ms: 1240, error_rate: 0.041 },
  { id: "remotive",   name: "Remotive",         tier: 2, status: "healthy",  pulled_24h: 1242, kept: 731,  kept_pct: 59, last_run: "4m ago",  avg_latency_ms: 620,  error_rate: 0.004 },
  { id: "wwr",        name: "We Work Remotely", tier: 2, status: "healthy",  pulled_24h: 487,  kept: 268,  kept_pct: 55, last_run: "8m ago",  avg_latency_ms: 510,  error_rate: 0.003 },
  { id: "ashby",      name: "Ashby",            tier: 1, status: "healthy",  pulled_24h: 921,  kept: 614,  kept_pct: 67, last_run: "3m ago",  avg_latency_ms: 460,  error_rate: 0.000 },
];

const SWB_LOG = [
  { t: "16:42:11", level: "info",  source: "greenhouse", msg: "Refresh complete · 412 new postings · 89 updated", n: 412 },
  { t: "16:41:55", level: "info",  source: "lever",      msg: "Refresh complete · 188 new postings · 41 updated", n: 188 },
  { t: "16:41:43", level: "info",  source: "ashby",      msg: "Refresh complete · 76 new postings", n: 76 },
  { t: "16:40:18", level: "warn",  source: "remoteok",   msg: "Slow response (1.8s) on /api/jobs · falling back to RSS", n: null },
  { t: "16:39:02", level: "info",  source: "remotive",   msg: "Refresh complete · 104 new postings", n: 104 },
  { t: "16:35:47", level: "info",  source: "classifier", msg: "Batch verified 312 postings · avg trust 81.4 · cost $0.42", n: 312 },
  { t: "16:31:20", level: "info",  source: "classifier", msg: "Batch verified 287 postings · avg trust 79.2 · cost $0.38", n: 287 },
  { t: "16:28:09", level: "warn",  source: "rules",      msg: "12 postings flagged as duplicates · same (company, title, posted_at)", n: 12 },
  { t: "16:24:51", level: "info",  source: "greenhouse", msg: "Refresh started · 142 companies in queue", n: null },
  { t: "16:22:14", level: "error", source: "remoteok",   msg: "HTTP 429 rate-limited · backoff 60s · will retry", n: null },
  { t: "16:18:33", level: "info",  source: "ranker",     msg: "Re-ranked surfaced feed · 312 postings live", n: 312 },
  { t: "16:15:08", level: "info",  source: "classifier", msg: "Prompt version v3.2 deployed · agreement on labeled set: 91.4%", n: null },
  { t: "16:10:42", level: "info",  source: "wwr",        msg: "Refresh complete · 38 new postings", n: 38 },
  { t: "16:08:21", level: "warn",  source: "rules",      msg: "Posting p_4421 flagged: Telegram contact in description", n: 1 },
];

const SWB_AUDIT = [
  { id: "p_4192", company: "Replit",          title: "Senior Software Engineer",        score: 94, verdict: "verified", rationale: "Verified ATS, worldwide remote, no scam signals." },
  { id: "p_4193", company: "Anonymous LLC",   title: "Data Entry Specialist",           score: 12, verdict: "rejected", rationale: "Gmail recruiter contact, 'earn $5000/week' phrasing, no domain." },
  { id: "p_4194", company: "Doist",           title: "iOS Engineer",                    score: 92, verdict: "verified", rationale: "All-remote company with documented handbook." },
  { id: "p_4195", company: "GlobalRemote Inc",title: "Customer Service Agent",          score: 28, verdict: "rejected", rationale: "Company has no verifiable domain or LinkedIn presence." },
  { id: "p_4196", company: "Buffer",          title: "Engineering Manager",             score: 95, verdict: "verified", rationale: "Buffer is a long-standing all-remote employer." },
  { id: "p_4197", company: "Acme Holdings",   title: "Remote Crypto Trader",            score: 5,  verdict: "rejected", rationale: "Crypto-investment 'job' with upfront deposit requirement." },
  { id: "p_4198", company: "Zapier",          title: "Senior PM, Platform",             score: 96, verdict: "verified", rationale: "Zapier is fully distributed, verified across 3 sources." },
];

const SWB_FEEDBACK = {
  up_7d: 1842,
  down_7d: 218,
  dismiss_7d: 94,
  apply_clicks_7d: 612,
  top_dismissed: [
    { company: "Acme Sales Co",  title: "Outbound SDR — Crypto",    reasons: ["Not actually remote", "Suspicious comp"] },
    { company: "GlobalHire",     title: "Virtual Assistant",         reasons: ["Spam-like phrasing"] },
    { company: "Cloudtech",      title: "DevOps Engineer",           reasons: ["Listed 'must be in US'"] },
  ],
};

// ——— Icons ———
function AdminIcon({ name, size = 14 }) {
  const paths = {
    refresh:     <path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M2.5 5.5V3m0 2.5H5M13.5 10.5V13m0-2.5H11" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    arrow_up:    <path d="M8 13V3m0 0l-3.5 3.5M8 3l3.5 3.5" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    arrow_down:  <path d="M8 3v10m0 0l-3.5-3.5M8 13l3.5-3.5" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    flat:        <path d="M3 8h10" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" />,
    info:        <><circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.3" fill="none"/><path d="M8 7.5v4M8 5v0.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></>,
    download:    <path d="M8 2v8m0 0l-3-3m3 3l3-3M3 13h10" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    play:        <path d="M5 3l8 5-8 5V3z" fill="currentColor"/>,
    arrow_right: <path d="M5 8h6m0 0l-2.5-2.5M11 8l-2.5 2.5" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" style={{ display: "inline-block", verticalAlign: "-2px" }}>
      {paths[name]}
    </svg>
  );
}

// ——— TopNav ———
function AdminTopNav({ onRunIngest, onExport }) {
  return (
    <nav className="topnav">
      <div className="topnav-inner">
        <div className="brand">
          <div className="brand-mark">S</div>
          <div>
            <div className="brand-name">Scale Without Borders</div>
            <div className="brand-sub" style={{ fontSize: 11.5, marginTop: -1 }}>Verified Remote · Canada</div>
          </div>
        </div>
        <div className="nav-tabs">
          <a href="/" className="nav-tab">Feed</a>
          <a href="/admin" className="nav-tab active">Admin</a>
        </div>
        <div className="nav-right">
          <span style={{ fontSize: 11.5, color: "var(--muted)" }} className="mono">
            env: <span style={{ color: "var(--ink)" }}>prod</span>
          </span>
          <button className="btn btn-ghost btn-sm" onClick={onRunIngest}>
            <AdminIcon name="play" size={11}/> Run ingest
          </button>
          <button className="btn btn-sm" onClick={onExport}>
            <AdminIcon name="download" size={13}/> Export
          </button>
        </div>
      </div>
    </nav>
  );
}

// ——— Kpi ———
function Kpi({ label, value, unit, delta, deltaDir, sub, highlight }) {
  return (
    <div className={"kpi" + (highlight ? " " + highlight : "")}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value}
        {unit && <span className="unit">{unit}</span>}
      </div>
      {delta != null && (
        <div className={"kpi-delta " + deltaDir}>
          <AdminIcon name={deltaDir === "up" ? "arrow_up" : deltaDir === "down" ? "arrow_down" : "flat"} size={11}/>
          {delta}
          {sub && <span style={{ color: "var(--muted)", fontWeight: 400, marginLeft: 4 }}>{sub}</span>}
        </div>
      )}
      {delta == null && sub && (
        <div className="kpi-delta flat">{sub}</div>
      )}
    </div>
  );
}

// ——— KpiStrip (uses real API data for what's available) ———
function KpiStrip({ postings }) {
  const activeCount = postings.length;
  const avgTrust = postings.length
    ? (postings.reduce((s, p) => s + p.trust_score, 0) / postings.length).toFixed(1)
    : "—";

  return (
    <div className="kpi-grid">
      <Kpi
        label="Verified rate (14d)"
        value="89.1"
        unit="%"
        delta="+1.4"
        deltaDir="up"
        sub="vs prior 14d · target ≥85"
        highlight="highlight"
      />
      <Kpi
        label="Active postings"
        value={activeCount > 0 ? activeCount : "312"}
        delta="+18"
        deltaDir="up"
        sub="since yesterday"
      />
      <Kpi
        label="Avg trust score"
        value={avgTrust !== "—" ? avgTrust : "81.4"}
        delta="+0.6"
        deltaDir="up"
      />
      <Kpi
        label="Classifier agreement"
        value="91.4"
        unit="%"
        delta="±0"
        deltaDir="flat"
        sub="prompt v3.2"
      />
      <Kpi
        label="Last ingest"
        value="3"
        unit="min"
        sub="next run ~ 4h"
      />
      <Kpi
        label="LLM cost today"
        value="$4.82"
        sub="MTD $92 / $200 budget"
      />
    </div>
  );
}

// ——— PipelineFunnel ———
function PipelineFunnel() {
  const funnel = SWB_FUNNEL;
  const max = funnel[0].count;
  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2 className="title">Pipeline funnel</h2>
          <p className="sub">Last 24 hours · Ingest → Verify → Rank → Deliver</p>
        </div>
        <div className="panel-head-right">
          <span className="pill pill-ghost mono" style={{ fontSize: 10.5 }}>24h</span>
        </div>
      </div>
      <div className="panel-body">
        <div className="pipeline-chain">
          <div className="stage">
            <div className="stage-label">Ingest</div>
            <div className="stage-count">10.4k</div>
          </div>
          <div className="arrow">→</div>
          <div className="stage">
            <div className="stage-label">Verify</div>
            <div className="stage-count">4.9k</div>
          </div>
          <div className="arrow">→</div>
          <div className="stage">
            <div className="stage-label">Rank</div>
            <div className="stage-count">1.8k</div>
          </div>
          <div className="arrow">→</div>
          <div className="stage" style={{ background: "var(--surface)", borderRadius: 6, border: "1px solid oklch(0.85 0.05 150)" }}>
            <div className="stage-label" style={{ color: "var(--trust-ink)" }}>Deliver</div>
            <div className="stage-count" style={{ color: "var(--trust-ink)" }}>312</div>
          </div>
        </div>

        <div className="funnel">
          {funnel.map((row, i) => {
            const isLast = i === funnel.length - 1;
            const cls = isLast ? "accent" : i >= 4 ? "dim" : "";
            return (
              <div className="funnel-row" key={row.stage}>
                <div className="stage-name">
                  <span className="stage-dot" style={{ background: isLast ? "var(--trust)" : i >= 4 ? "oklch(0.55 0.04 270)" : "var(--ink)" }}></span>
                  {row.stage}
                </div>
                <div className="funnel-bar-track">
                  <div className={"funnel-bar " + cls} style={{ width: ((row.count / max) * 100) + "%" }}>
                    {row.pct.toFixed(1)}%
                  </div>
                </div>
                <div className="funnel-count">{row.count.toLocaleString()}</div>
                <div className="funnel-pct">
                  {i > 0 ? ((row.count / funnel[i - 1].count) * 100).toFixed(0) + "%" : "—"}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--muted)", marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
          <span>Biggest drop-off: <b style={{ color: "var(--ink)" }}>Ranked → Surfaced</b> (filters: trust ≥ 70, fresh ≤ 14d)</span>
          <span className="mono">3.0% end-to-end</span>
        </div>
      </div>
    </div>
  );
}

// ——— SourcesPanel ———
function SourcesPanel() {
  return (
    <div className="panel full">
      <div className="panel-head">
        <div>
          <h2 className="title">Source health</h2>
          <p className="sub">Per-source ingestion volume, latency, and kept rate · last 24h</p>
        </div>
        <div className="panel-head-right">
          <button className="btn btn-sm btn-ghost">
            <AdminIcon name="refresh" size={11}/> Re-run all
          </button>
        </div>
      </div>
      <div className="panel-body no-pad">
        <table className="src-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Status</th>
              <th>Last run</th>
              <th className="num">Pulled</th>
              <th className="num">Kept</th>
              <th>Kept rate</th>
              <th className="num">Latency</th>
              <th className="num">Error rate</th>
            </tr>
          </thead>
          <tbody>
            {SWB_SOURCES.map(s => (
              <tr key={s.id}>
                <td>
                  <div className="src-name">
                    <div className="mini-logo">{s.name.charAt(0)}</div>
                    <div>
                      <div style={{ fontWeight: 500 }}>{s.name}</div>
                      <div className="tier-tag" style={{ marginTop: 2 }}>tier {s.tier}</div>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={"status-dot " + s.status}>
                    {s.status.charAt(0).toUpperCase() + s.status.slice(1)}
                  </span>
                </td>
                <td style={{ color: "var(--muted)", fontSize: 12 }}>{s.last_run}</td>
                <td className="num">{s.pulled_24h.toLocaleString()}</td>
                <td className="num">{s.kept.toLocaleString()}</td>
                <td>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span className="mono" style={{ fontSize: 12, color: "var(--ink)" }}>{s.kept_pct}%</span>
                    <span className="bar-inline">
                      <i style={{ width: s.kept_pct + "%", background: s.kept_pct > 60 ? "var(--trust)" : "var(--ink)" }}/>
                    </span>
                  </div>
                </td>
                <td className="num">{s.avg_latency_ms}ms</td>
                <td className="num" style={{ color: s.error_rate > 0.02 ? "var(--warn-ink)" : s.error_rate > 0 ? "var(--muted)" : "var(--trust-ink)" }}>
                  {(s.error_rate * 100).toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ——— TrustHistogram ———
function TrustHistogram({ postings }) {
  // Use real data if available, otherwise fall back to static
  const hist = postings.length > 0
    ? (() => {
        const buckets = [
          { bucket: "0-9", count: 0 }, { bucket: "10-19", count: 0 },
          { bucket: "20-29", count: 0 }, { bucket: "30-39", count: 0 },
          { bucket: "40-49", count: 0 }, { bucket: "50-59", count: 0 },
          { bucket: "60-69", count: 0 }, { bucket: "70-79", count: 0 },
          { bucket: "80-89", count: 0 }, { bucket: "90-100", count: 0 },
        ];
        postings.forEach(p => {
          const idx = Math.min(9, Math.floor(p.trust_score / 10));
          buckets[idx].count++;
        });
        return buckets;
      })()
    : SWB_TRUST_HIST;

  const max = Math.max(...hist.map(b => b.count));
  const total = hist.reduce((s, b) => s + b.count, 0);
  const above70 = hist.filter((_, i) => i >= 7).reduce((s, b) => s + b.count, 0);
  const pct = total > 0 ? ((above70 / total) * 100).toFixed(1) : "0.0";
  const thresholdLeft = (7 / 10) * 100;

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2 className="title">Trust score distribution</h2>
          <p className="sub">All postings classified in the last 24h · n = {total.toLocaleString()}</p>
        </div>
        <div className="panel-head-right">
          <span className="pill pill-trust mono" style={{ fontSize: 10.5 }}>≥70 surfaceable</span>
        </div>
      </div>
      <div className="panel-body">
        <div style={{ position: "relative" }}>
          <div className="histogram">
            <div className="hist-threshold-line" style={{ left: "calc(" + thresholdLeft + "% - 3px)" }}>
              <span>cutoff 70</span>
            </div>
            {hist.map((b, i) => (
              <div
                key={b.bucket}
                className={"hist-bar" + (i >= 7 ? (i === 9 ? " threshold" : "") : " below")}
                style={{ height: max > 0 ? ((b.count / max) * 100) + "%" : "4px" }}
              >
                <span className="tip">{b.count} · {b.bucket}</span>
              </div>
            ))}
          </div>
          <div className="hist-axis">
            {hist.map(b => <span key={b.bucket}>{b.bucket}</span>)}
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--muted)", marginTop: 16, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
          <span><span className="mono" style={{ color: "var(--trust-ink)", fontWeight: 600 }}>{pct}%</span> of postings scored ≥ 70 and were surfaceable</span>
          <span><span className="mono" style={{ color: "var(--ink)" }}>{above70.toLocaleString()}</span> postings above cutoff</span>
        </div>
      </div>
    </div>
  );
}

// ——— VerifiedRateSpark ———
function VerifiedRateSpark() {
  const ts = SWB_VERIFIED_TIMESERIES;
  const w = 100, h = 60;
  const min = 82, max = 92;
  const pts = ts.map((v, i) => [
    (i / (ts.length - 1)) * w,
    h - ((v - min) / (max - min)) * h,
  ]);
  const path = pts.map((p, i) => (i === 0 ? "M" : "L") + " " + p[0].toFixed(2) + " " + p[1].toFixed(2)).join(" ");
  const areaPath = path + " L " + w + " " + h + " L 0 " + h + " Z";
  const last = ts[ts.length - 1];
  const first = ts[0];
  const delta = (last - first).toFixed(1);

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2 className="title">Verified rate · 14d</h2>
          <p className="sub">Daily share of postings clearing all rules + LLM verification</p>
        </div>
        <div className="panel-head-right">
          <span className="display-num" style={{ fontSize: 32, color: "var(--trust-ink)" }}>{last}%</span>
        </div>
      </div>
      <div className="panel-body">
        <div className="sparkline-block">
          <svg className="sparkline-svg" viewBox={"0 0 " + w + " " + h} preserveAspectRatio="none">
            <defs>
              <linearGradient id="sparkfill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="oklch(0.62 0.13 150)" stopOpacity="0.18"/>
                <stop offset="100%" stopColor="oklch(0.62 0.13 150)" stopOpacity="0"/>
              </linearGradient>
            </defs>
            <line
              x1="0" x2={w}
              y1={h - ((85 - min) / (max - min)) * h}
              y2={h - ((85 - min) / (max - min)) * h}
              stroke="oklch(0.78 0.04 75)"
              strokeWidth="0.6"
              strokeDasharray="2 2"
              vectorEffect="non-scaling-stroke"
            />
            <path d={areaPath} fill="url(#sparkfill)"/>
            <path d={path} fill="none" stroke="oklch(0.62 0.13 150)" strokeWidth="1.4" vectorEffect="non-scaling-stroke" strokeLinejoin="round"/>
            {pts.map((p, i) => i === pts.length - 1 ? (
              <circle key={i} cx={p[0]} cy={p[1]} r="1.6" fill="oklch(0.62 0.13 150)" vectorEffect="non-scaling-stroke"/>
            ) : null)}
          </svg>
          <div className="sparkline-axis">
            <span>14d ago</span>
            <span>7d ago</span>
            <span>today</span>
          </div>
        </div>
        <div style={{ display: "flex", gap: 24, marginTop: 16, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
          <div>
            <div className="label-tiny">Avg 14d</div>
            <div className="display-num" style={{ fontSize: 22, marginTop: 4 }}>87.4<span style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--muted)" }}>%</span></div>
          </div>
          <div>
            <div className="label-tiny">Δ vs first day</div>
            <div className="display-num" style={{ fontSize: 22, marginTop: 4, color: "var(--trust-ink)" }}>+{delta}<span style={{ fontFamily: "var(--font-ui)", fontSize: 12, color: "var(--muted)" }}>pp</span></div>
          </div>
          <div>
            <div className="label-tiny">Target</div>
            <div className="display-num" style={{ fontSize: 22, marginTop: 4, color: "var(--muted)" }}>85<span style={{ fontFamily: "var(--font-ui)", fontSize: 12 }}>%</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ——— IngestionLog ———
function IngestionLog() {
  const [filter, setFilter] = useState("all");
  const filtered = SWB_LOG.filter(l => filter === "all" || l.level === filter);
  return (
    <div className="panel full">
      <div className="panel-head">
        <div>
          <h2 className="title">Ingestion log</h2>
          <p className="sub">Real-time stream of pipeline events</p>
        </div>
        <div className="panel-head-right">
          <div className="range-toggle">
            <button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>All</button>
            <button className={filter === "info" ? "active" : ""} onClick={() => setFilter("info")}>Info</button>
            <button className={filter === "warn" ? "active" : ""} onClick={() => setFilter("warn")}>Warn</button>
            <button className={filter === "error" ? "active" : ""} onClick={() => setFilter("error")}>Error</button>
          </div>
        </div>
      </div>
      <div className="panel-body no-pad">
        <div className="log-list">
          {filtered.map((l, i) => (
            <div className="log-row" key={i}>
              <span className="t">{l.t}</span>
              <span className={"lvl " + l.level}>{l.level}</span>
              <span className="src">{l.source}</span>
              <span className="msg">{l.msg}</span>
              <span className="n">{l.n != null ? "n=" + l.n : ""}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ——— AuditPanel (uses real postings if available, otherwise mock) ———
function AuditPanel({ postings }) {
  // Build audit rows from real data or fall back to static mock
  const audit = postings.length > 0
    ? postings.slice(0, 7).map(p => ({
        id: "p_" + p.id,
        company: p.company,
        title: p.title,
        score: p.trust_score,
        verdict: p.trust_score >= 70 ? "verified" : "rejected",
        rationale: p.rationale || "No rationale available.",
      }))
    : SWB_AUDIT;

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2 className="title">Classifier audit</h2>
          <p className="sub">Latest LLM verdicts with rationale · sampled for review</p>
        </div>
        <div className="panel-head-right">
          <span className="pill pill-ghost mono" style={{ fontSize: 10.5 }}>v3.2</span>
        </div>
      </div>
      <div className="panel-body no-pad">
        <div className="audit-list">
          {audit.map(a => (
            <div className="audit-row" key={a.id}>
              <div className={"score-pill " + (a.verdict === "verified" ? "ok" : "bad")}>
                {a.score}
              </div>
              <div>
                <div className="title">{a.title}</div>
                <div className="company">{a.company} · <span className="mono">{a.id}</span></div>
                <div className="rationale">{a.rationale}</div>
              </div>
              <div className={"verdict-tag " + (a.verdict === "verified" ? "ok" : "bad")}>
                {a.verdict}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ——— FeedbackPanel ———
function FeedbackPanel() {
  const fb = SWB_FEEDBACK;
  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2 className="title">Member feedback · 7d</h2>
          <p className="sub">Signals from the user feed</p>
        </div>
      </div>
      <div className="panel-body no-pad">
        <div className="feedback-row">
          <div className="feedback-cell">
            <div className="num" style={{ color: "var(--trust-ink)" }}>{fb.up_7d.toLocaleString()}</div>
            <div className="lbl">👍 Helpful</div>
          </div>
          <div className="feedback-cell">
            <div className="num" style={{ color: "var(--danger-ink)" }}>{fb.down_7d}</div>
            <div className="lbl">👎 Not helpful</div>
          </div>
          <div className="feedback-cell">
            <div className="num">{fb.dismiss_7d}</div>
            <div className="lbl">Dismissed</div>
          </div>
          <div className="feedback-cell">
            <div className="num">{fb.apply_clicks_7d}</div>
            <div className="lbl">Apply clicks</div>
          </div>
        </div>

        <div style={{ padding: "14px 20px 6px" }}>
          <div className="label-tiny" style={{ marginBottom: 8 }}>Top-dismissed postings — used to retrain classifier</div>
        </div>
        <div className="dismissed-list">
          {fb.top_dismissed.map((d, i) => (
            <div className="dismissed-row" key={i}>
              <span className="x-tag">×{Math.floor(20 - i * 6)}</span>
              <div>
                <div className="ttl">{d.title}</div>
                <div className="meta">{d.company} · {d.reasons.join(" · ")}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ——— ControlRow ———
function ControlRow({ label, value, unit, hint, mono }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
      <div>
        <div style={{ fontSize: 12.5, color: "var(--ink)", fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 2 }}>{hint}</div>
      </div>
      <div style={{ fontFamily: mono ? "var(--font-mono)" : "var(--font-ui)", fontSize: 13, color: "var(--ink)" }}>
        {value}{unit && <span style={{ color: "var(--muted)", marginLeft: 3, fontSize: 12 }}>{unit}</span>}
      </div>
    </div>
  );
}

// ——— Admin Page ———
export default function AdminPage() {
  const [range, setRange] = useState("24h");
  const [postings, setPostings] = useState([]);
  const [ingestRunning, setIngestRunning] = useState(false);

  useEffect(() => {
    fetch(API_BASE + "/api/postings?days=14&limit=100")
      .then(r => r.ok ? r.json() : [])
      .then(data => setPostings(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  async function handleRunIngest() {
    setIngestRunning(true);
    try { await fetch(API_BASE + "/api/refresh", { method: "POST" }); } catch (_) {}
    setIngestRunning(false);
  }

  function handleExport() {
    window.open(API_BASE + "/api/export/csv?days=14", "_blank");
  }

  return (
    <>
      <AdminTopNav onRunIngest={handleRunIngest} onExport={handleExport}/>
      <div className="admin-shell">
        <header className="admin-header">
          <div className="admin-title-block">
            <div className="label-tiny">Operations · Pipeline</div>
            <h1 className="admin-title">Verification <em>health</em></h1>
            <p style={{ color: "var(--muted)", margin: "6px 0 0", fontSize: 13 }}>
              Aggregate metrics for ingestion, classification, ranking, and member delivery.
            </p>
          </div>
          <div className="admin-header-right">
            <div className="range-toggle">
              {["1h", "24h", "7d", "30d"].map(r => (
                <button key={r} className={range === r ? "active" : ""} onClick={() => setRange(r)}>
                  {r}
                </button>
              ))}
            </div>
          </div>
        </header>

        <KpiStrip postings={postings}/>

        <div className="admin-grid">
          <PipelineFunnel/>
          <VerifiedRateSpark/>

          <SourcesPanel/>

          <TrustHistogram postings={postings}/>
          <FeedbackPanel/>

          <IngestionLog/>

          <AuditPanel postings={postings}/>
          <div className="panel" style={{ display: "flex", flexDirection: "column" }}>
            <div className="panel-head">
              <div>
                <h2 className="title">Run controls</h2>
                <p className="sub">Operator levers · effect is immediate</p>
              </div>
            </div>
            <div className="panel-body" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <ControlRow label="Trust cutoff" value="70" mono unit="/100" hint="Postings below are dropped"/>
              <ControlRow label="Max age" value="14" unit="days" hint="Postings older than this are removed"/>
              <ControlRow label="Refresh cadence" value="4h" hint="Cron interval across all sources"/>
              <ControlRow label="LLM model" value="claude-sonnet-4-5" mono hint="Classifier model for verification"/>
              <ControlRow label="Prompt version" value="v3.2" mono hint="91.4% agreement on labeled set"/>
              <ControlRow label="Budget guardrail" value="$200" unit="/ month" hint="Pauses runs above this threshold"/>
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button className="btn btn-primary btn-sm" style={{ flex: 1 }} onClick={handleRunIngest} disabled={ingestRunning}>
                  <AdminIcon name="play" size={11}/> {ingestRunning ? "Running…" : "Trigger full re-classification"}
                </button>
                <button className="btn btn-sm" style={{ flex: 1 }} onClick={handleExport}>
                  <AdminIcon name="download" size={12}/> Export labeled set
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
