"use client";

import { useState, useMemo, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://ai-hackaton-06yr.onrender.com";

const ROLE_FAMILIES = ["Engineering", "Design", "Product", "Marketing", "Data", "Sales", "Support", "HR", "Finance"];
const SENIORITIES = ["Junior", "Mid", "Senior"];
const SOURCES = [
  { id: "greenhouse", name: "Greenhouse" },
  { id: "lever", name: "Lever" },
  { id: "remoteok", name: "RemoteOK" },
  { id: "remotive", name: "Remotive" },
  { id: "ashby", name: "Ashby" },
  { id: "wwr", name: "We Work Remotely" },
  { id: "workingnomads", name: "Working Nomads" },
];

function daysAgo(posted_at) {
  if (!posted_at) return 999;
  const ms = Date.now() - new Date(posted_at).getTime();
  return Math.max(0, Math.round(ms / 86400000));
}

function hasSponsorship(signals) {
  return signals.some(s => /sponsor/i.test(s));
}

function isCanadaEligible(location_raw) {
  return !!(location_raw && /canada|worldwide|global|north america/i.test(location_raw));
}

function Icon({ name, size = 14 }) {
  const paths = {
    check: <path d="M3 8l3.5 3.5L13 4" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    sparkle: <path d="M8 1.5L9.2 6.8L14.5 8L9.2 9.2L8 14.5L6.8 9.2L1.5 8L6.8 6.8L8 1.5Z" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinejoin="round" />,
    refresh: <path d="M3 8a5 5 0 019-3l1.5 1.5M13 8a5 5 0 01-9 3L2.5 9.5M2.5 5.5V3m0 2.5H5M13.5 10.5V13m0-2.5H11" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    download: <path d="M8 2v8m0 0l-3-3m3 3l3-3M3 13h10" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    search: <><circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.4" fill="none" /><path d="M10.5 10.5L13 13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></>,
    pin: <path d="M8 14s4.5-4 4.5-7.5a4.5 4.5 0 10-9 0C3.5 10 8 14 8 14z M8 8.5a2 2 0 100-4 2 2 0 000 4z" stroke="currentColor" strokeWidth="1.2" fill="none" strokeLinejoin="round" />,
    bookmark: <path d="M4 2.5h8v11l-4-2.5-4 2.5v-11z" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinejoin="round" />,
    bookmark_filled: <path d="M4 2.5h8v11l-4-2.5-4 2.5v-11z" fill="currentColor" />,
    thumbs_up: <path d="M5 14V7m0 0l3-5 1 1v3h3.5a1 1 0 011 1.2l-1 5a1 1 0 01-1 .8H5z" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinejoin="round" />,
    thumbs_down: <path d="M5 2v7m0 0l3 5 1-1v-3h3.5a1 1 0 001-1.2l-1-5a1 1 0 00-1-.8H5z" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinejoin="round" />,
    x: <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />,
    arrow: <path d="M3 8h10m0 0l-4-4m4 4l-4 4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />,
    chevron: <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" />,
    globe: <><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.3" fill="none" /><path d="M2.5 8h11M8 2.5c2 2.5 2 8.5 0 11M8 2.5c-2 2.5-2 8.5 0 11" stroke="currentColor" strokeWidth="1.2" fill="none" /></>,
    info: <><circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.3" fill="none" /><path d="M8 7.5v4M8 5v0.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" /></>,
    bolt: <path d="M9 1L3 9h4l-1 6 6-8H8l1-6z" stroke="currentColor" strokeWidth="1.3" fill="none" strokeLinejoin="round" />,
    shield: <path d="M8 1.5l5.5 2v4c0 3.5-2.5 6.2-5.5 7-3-0.8-5.5-3.5-5.5-7v-4l5.5-2z M5.5 8L7 9.5L10.5 6" stroke="currentColor" strokeWidth="1.3" fill="none" strokeLinejoin="round" strokeLinecap="round" />,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" style={{ display: "inline-block", verticalAlign: "-2px" }}>
      {paths[name]}
    </svg>
  );
}

function TopNav({ active = "feed", onRefresh, onExport, refreshing }) {
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
          <a href="/" className={"nav-tab" + (active === "feed" ? " active" : "")}>Feed</a>
          <a href="/admin" className={"nav-tab" + (active === "admin" ? " active" : "")}>Admin</a>
        </div>
        <div className="nav-right">
          <button className="btn btn-ghost btn-sm" onClick={onRefresh} disabled={refreshing}>
            <Icon name="refresh" size={13} /> {refreshing ? "Refreshing…" : "Refresh"}
          </button>
          <button className="btn btn-sm" onClick={onExport}>
            <Icon name="download" size={13} /> Export CSV
          </button>
        </div>
      </div>
    </nav>
  );
}

function FeedHero({ visibleCount, lastRefresh, newcomerCount, sponsorCount }) {
  return (
    <section className="feed-hero">
      <div className="hero-eyebrow">
        <span className="dot-pulse"></span>
        <span>Pipeline live · updated {lastRefresh}</span>
        <span style={{ color: "var(--border-strong)" }}>·</span>
        <span>Classifier v3.2 · 91.4% agreement</span>
      </div>
      <h1 className="hero-title">Remote work that actually <em>welcomes</em> newcomers.</h1>
      <p className="hero-sub">
        Every posting is pulled from a verified employer, scored by AI for legitimacy and remote
        authenticity, then audited by humans before it reaches you.
      </p>
      <div className="hero-stats">
        <div className="hero-stat">
          <div className="num">{visibleCount}</div>
          <div className="lbl">verified roles in feed</div>
        </div>
        <div className="hero-stat">
          <div className="num">{newcomerCount}</div>
          <div className="lbl">newcomer-friendly</div>
        </div>
        <div className="hero-stat">
          <div className="num">{sponsorCount}</div>
          <div className="lbl">offer sponsorship</div>
        </div>
        <div className="hero-stat">
          <div className="num" style={{ color: "var(--trust-ink)" }}>89%</div>
          <div className="lbl">14-day verified rate</div>
        </div>
      </div>
    </section>
  );
}

function FilterRail({ filters, setFilters, counts }) {
  const toggleArr = (key, value) => {
    setFilters(f => {
      const arr = f[key];
      return { ...f, [key]: arr.includes(value) ? arr.filter(v => v !== value) : [...arr, value] };
    });
  };

  return (
    <aside className="rail">
      <div className="rail-group">
        <div className="search">
          <Icon name="search" size={13} />
          <input
            placeholder="Search roles, companies…"
            value={filters.query}
            onChange={e => setFilters(f => ({ ...f, query: e.target.value }))}
          />
          {filters.query && (
            <button
              onClick={() => setFilters(f => ({ ...f, query: "" }))}
              style={{ background: "transparent", border: 0, padding: 0, color: "var(--muted)", cursor: "pointer" }}
            >
              <Icon name="x" size={11} />
            </button>
          )}
        </div>
      </div>

      <div className="rail-group">
        <div className="label-tiny">Role family</div>
        <button
          className={"rail-chip" + (filters.roles.length === 0 ? " active" : "")}
          onClick={() => setFilters(f => ({ ...f, roles: [] }))}
        >
          <span>All roles</span>
          <span className="count">{counts.total}</span>
        </button>
        {ROLE_FAMILIES.map(r => counts.byRole[r] ? (
          <button
            key={r}
            className={"rail-chip" + (filters.roles.includes(r) ? " active" : "")}
            onClick={() => toggleArr("roles", r)}
          >
            <span>{r}</span>
            <span className="count">{counts.byRole[r] || 0}</span>
          </button>
        ) : null)}
      </div>

      <div className="rail-group">
        <div className="label-tiny">Seniority</div>
        {SENIORITIES.map(s => (
          <label key={s} className="checkbox-row">
            <input
              type="checkbox"
              checked={filters.seniority.includes(s)}
              onChange={() => toggleArr("seniority", s)}
            />
            <span>{s}</span>
          </label>
        ))}
      </div>

      <div className="rail-group">
        <div className="label-tiny">Trust score</div>
        <div className="slider-row">
          <div className="slider-head">
            <span style={{ color: "var(--muted)" }}>Minimum</span>
            <span className="v">{filters.minTrust}+</span>
          </div>
          <input
            type="range" min={70} max={100} step={1}
            value={filters.minTrust}
            onChange={e => setFilters(f => ({ ...f, minTrust: +e.target.value }))}
          />
        </div>
      </div>

      <div className="rail-group">
        <div className="label-tiny">Posted within</div>
        {[
          { v: 1, label: "24 hours" },
          { v: 3, label: "3 days" },
          { v: 7, label: "7 days" },
          { v: 14, label: "14 days" },
        ].map(o => (
          <button
            key={o.v}
            className={"rail-chip" + (filters.maxDays === o.v ? " active" : "")}
            onClick={() => setFilters(f => ({ ...f, maxDays: o.v }))}
          >
            <span>{o.label}</span>
          </button>
        ))}
      </div>

      <div className="rail-group">
        <div className="label-tiny">Newcomer signals</div>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={filters.newcomerOnly}
            onChange={e => setFilters(f => ({ ...f, newcomerOnly: e.target.checked }))}
          />
          <span>Newcomer-friendly only</span>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={filters.sponsorshipOnly}
            onChange={e => setFilters(f => ({ ...f, sponsorshipOnly: e.target.checked }))}
          />
          <span>Offers visa sponsorship</span>
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={filters.canadaOnly}
            onChange={e => setFilters(f => ({ ...f, canadaOnly: e.target.checked }))}
          />
          <span>Canada-eligible</span>
        </label>
      </div>

      <div className="rail-group">
        <div className="label-tiny">Source</div>
        {SOURCES.map(s => counts.bySource[s.id] ? (
          <label key={s.id} className="checkbox-row">
            <input
              type="checkbox"
              checked={filters.sources.length === 0 || filters.sources.includes(s.id)}
              onChange={() => toggleArr("sources", s.id)}
            />
            <span>{s.name}</span>
            <span className="count" style={{ marginLeft: "auto", color: "var(--muted-2)", fontSize: 11.5 }}>
              {counts.bySource[s.id] || 0}
            </span>
          </label>
        ) : null)}
      </div>
    </aside>
  );
}

function cleanLocation(raw: string | undefined | null): string {
  if (!raw) return "";
  // Detect character-by-character join bug from backend (Python's ", ".join(str))
  // Pattern: starts with single letter, comma, space, single letter
  let loc = /^[A-Za-z], [A-Za-z], /.test(raw) ? raw.replace(/, /g, "") : raw;
  // Truncate to first meaningful region for display (e.g. "London, England, UK" → "London")
  if (loc.length > 28) {
    const parts = loc.split(",");
    return parts[0].trim() + (parts.length > 1 ? ", …" : "");
  }
  return loc;
}

function cleanDescription(raw) {
  if (!raw) return "";
  // Decode common HTML entities
  let s = raw
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, " ");
  // Strip HTML tags
  s = s.replace(/<[^>]+>/g, " ");
  // Collapse whitespace
  s = s.replace(/\s+/g, " ").trim();
  // Fix space-before-punctuation artifact from HTML stripping
  s = s.replace(/ ([,;:!?])/g, "$1");
  // Strip common boilerplate section headers at the start
  s = s.replace(/^(about the (job|role|position|company|team)|job description|overview|position summary)[:\s]*/i, "");
  s = s.trim();
  // Truncate to 200 chars at a word boundary
  if (s.length > 200) {
    s = s.slice(0, 200).replace(/\s\S*$/, "") + "\u2026";
  }
  return s;
}

function PostingCard({ p, saved, voted, onSave, onVote, onDismiss, dismissed, compact }) {
  if (dismissed) return null;
  const days = daysAgo(p.posted_at);
  const sponsorship = hasSponsorship(p.newcomer_friendly_signals);
  const trustHue = p.trust_score >= 90 ? "var(--trust-ink)" : p.trust_score >= 80 ? "var(--info-ink)" : "var(--warn-ink)";
  const trustLabel = p.trust_score >= 90 ? "High trust" : p.trust_score >= 80 ? "Verified" : "Trusted";
  const initial = p.company.charAt(0);
  const remoteConf = Math.min(1, Math.max(0, p.trust_score / 100));
  const roleFamily = p.role_family
    ? p.role_family.charAt(0).toUpperCase() + p.role_family.slice(1)
    : "Other";
  const seniorityDisplay = p.seniority
    ? p.seniority.charAt(0).toUpperCase() + p.seniority.slice(1)
    : null;
  const sourceName = SOURCES.find(s => s.id === p.source)?.name || p.source;
  const snippet = cleanDescription(p.description);

  return (
    <article className="card">
      <div className="card-top">
        <div className="logo-mark">{initial}</div>
        <div className="card-head">
          <div className="card-meta-top">
            <span>{roleFamily.toUpperCase()}</span>
            <span className="sep">·</span>
            <span>{days === 0 ? "today" : days === 1 ? "1d ago" : days + "d ago"}</span>
            <span className="sep">·</span>
            <span style={{ textTransform: "capitalize" }}>via {sourceName}</span>
          </div>
          <h3 className="card-title">{p.title}</h3>
          <div className="card-company">
            <span>{p.company}</span>
            <span style={{ color: "var(--border-strong)" }}>·</span>
            <Icon name="pin" size={11} />
            <span style={{ color: "var(--muted)" }}>{cleanLocation(p.location_raw) || "Remote"}</span>
            <span className="verified-tick" title="Verified employer">
              <Icon name="check" size={11} />
            </span>
          </div>
        </div>
        <div className="trust-gauge">
          <div className="score" style={{ color: trustHue }}>
            {p.trust_score}<span className="of">/100</span>
          </div>
          <div className="bar"><i style={{ width: p.trust_score + "%" }} /></div>
          <div className="lbl" style={{ color: trustHue }}>{trustLabel}</div>
        </div>
      </div>

      <div className="card-body">
        <div className="tag-row">
          <span className="pill pill-info">
            <Icon name="globe" size={10} /> Verified Remote
          </span>
          {p.newcomer_friendly_signals.length > 0 && (
            <span className="pill pill-newcomer">
              <span className="pill-dot" /> Newcomer-friendly
            </span>
          )}
          {sponsorship && (
            <span className="pill pill-violet">
              <Icon name="shield" size={10} /> Sponsorship
            </span>
          )}
          {seniorityDisplay && seniorityDisplay !== "Mid" && seniorityDisplay !== "Any" && (
            <span className="pill pill-ghost">{seniorityDisplay}</span>
          )}
          {days <= 2 && (
            <span className="pill pill-trust">
              <Icon name="bolt" size={10} /> Fresh
            </span>
          )}
        </div>

        {!compact && (
          <>
            <p className="snippet">{snippet}</p>

            <div className="why-panel">
              <div className="why-text">
                <span className="icon"><Icon name="sparkle" size={12} /></span>
                <span>
                  <b style={{ color: "var(--ink)", fontWeight: 500 }}>Why we surfaced this</b> — {p.rationale}
                </span>
              </div>
              <div className="classifier-mini">
                <div>
                  <span>remote</span>
                  <b>{Math.round(remoteConf * 100)}%</b>
                </div>
                <div>
                  <span>scam</span>
                  <b style={{ color: p.scam_likelihood > 0.05 ? "var(--warn-ink)" : "var(--ink)" }}>
                    {Math.round(p.scam_likelihood * 100)}%
                  </b>
                </div>
                <div>
                  <span>clarity</span>
                  <b>85%</b>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="card-foot">
        <div className="salary" style={{ color: "var(--muted)", fontSize: 12 }}>
          {p.source_url && p.source_url !== "#"
            ? <a href={p.source_url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--muted)", textDecoration: "underline dotted" }}>View original posting</a>
            : <span>—</span>
          }
        </div>
        <div className="card-foot-right">
          <button
            className={"icon-btn" + (voted === "up" ? " active" : "")}
            title="Helpful"
            onClick={() => onVote(p.id, voted === "up" ? null : "up")}
          >
            <Icon name="thumbs_up" size={13} />
          </button>
          <button
            className={"icon-btn danger" + (voted === "down" ? " active" : "")}
            title="Not helpful"
            onClick={() => onVote(p.id, voted === "down" ? null : "down")}
          >
            <Icon name="thumbs_down" size={13} />
          </button>
          <button
            className={"icon-btn" + (saved ? " active" : "")}
            title="Save"
            onClick={() => onSave(p.id)}
          >
            <Icon name={saved ? "bookmark_filled" : "bookmark"} size={13} />
          </button>
          <button
            className="icon-btn"
            title="Dismiss"
            onClick={() => onDismiss(p.id)}
          >
            <Icon name="x" size={12} />
          </button>
          <a
            href={p.source_url && p.source_url !== "#" ? p.source_url : "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary btn-sm"
            style={{ marginLeft: 4, textDecoration: "none" }}
          >
            Apply <Icon name="arrow" size={11} />
          </a>
        </div>
      </div>
    </article>
  );
}

export default function FeedPage() {
  const [postings, setPostings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState("");

  const [filters, setFilters] = useState({
    query: "",
    roles: [],
    seniority: [],
    sources: [],
    minTrust: 70,
    maxDays: 14,
    newcomerOnly: false,
    sponsorshipOnly: false,
    canadaOnly: false,
  });
  const [sort, setSort] = useState("match");
  const [compact, setCompact] = useState(false);
  const [saved, setSaved] = useState({});
  const [votes, setVotes] = useState({});
  const [dismissed, setDismissed] = useState({});

  async function fetchPostings() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ days: "14", limit: "100" });
      const res = await fetch(API_BASE + "/api/postings?" + params);
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      setPostings(data);
      setLastRefresh(new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }));
    } catch (e) {
      setError("Could not load postings. The pipeline may still be running — try refreshing.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    try { await fetch(API_BASE + "/api/refresh", { method: "POST" }); } catch (_) { }
    await fetchPostings();
    setRefreshing(false);
  }

  async function handleVote(id, signal) {
    setVotes(vs => ({ ...vs, [id]: signal }));
    if (signal) {
      try {
        await fetch(API_BASE + "/api/feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ posting_id: id, signal }),
        });
      } catch (_) { }
    }
  }

  function handleExport() {
    window.open(API_BASE + "/api/export/csv?days=14", "_blank");
  }

  useEffect(() => { fetchPostings(); }, []);

  const filtered = useMemo(() => {
    let list = postings.filter(p => {
      const days = daysAgo(p.posted_at);
      if (filters.query) {
        const q = filters.query.toLowerCase();
        if (!p.title.toLowerCase().includes(q) && !p.company.toLowerCase().includes(q) && !(p.description || "").toLowerCase().includes(q)) return false;
      }
      const rf = p.role_family ? p.role_family.charAt(0).toUpperCase() + p.role_family.slice(1) : "Other";
      if (filters.roles.length && !filters.roles.includes(rf)) return false;
      const sen = p.seniority ? p.seniority.charAt(0).toUpperCase() + p.seniority.slice(1) : null;
      if (filters.seniority.length && (!sen || !filters.seniority.includes(sen))) return false;
      if (filters.sources.length && !filters.sources.includes(p.source)) return false;
      if (p.trust_score < filters.minTrust) return false;
      if (days > filters.maxDays) return false;
      if (filters.newcomerOnly && p.newcomer_friendly_signals.length === 0) return false;
      if (filters.sponsorshipOnly && !hasSponsorship(p.newcomer_friendly_signals)) return false;
      if (filters.canadaOnly && !isCanadaEligible(p.location_raw)) return false;
      return true;
    });
    if (sort === "trust") list = [...list].sort((a, b) => b.trust_score - a.trust_score);
    else if (sort === "fresh") list = [...list].sort((a, b) => daysAgo(a.posted_at) - daysAgo(b.posted_at));
    else list = [...list].sort((a, b) =>
      (b.trust_score + b.newcomer_friendly_signals.length * 3 - daysAgo(b.posted_at)) -
      (a.trust_score + a.newcomer_friendly_signals.length * 3 - daysAgo(a.posted_at))
    );
    return list;
  }, [postings, filters, sort]);

  const counts = useMemo(() => {
    const byRole = {}, bySource = {};
    postings.forEach(p => {
      const rf = p.role_family ? p.role_family.charAt(0).toUpperCase() + p.role_family.slice(1) : "Other";
      byRole[rf] = (byRole[rf] || 0) + 1;
      bySource[p.source] = (bySource[p.source] || 0) + 1;
    });
    return { byRole, bySource, total: postings.length };
  }, [postings]);

  const newcomerCount = postings.filter(p => p.newcomer_friendly_signals.length > 0).length;
  const sponsorCount = postings.filter(p => hasSponsorship(p.newcomer_friendly_signals)).length;
  const visibleCount = filtered.filter(p => !dismissed[p.id]).length;

  return (
    <>
      <TopNav active="feed" onRefresh={handleRefresh} onExport={handleExport} refreshing={refreshing} />
      <FeedHero visibleCount={visibleCount} lastRefresh={lastRefresh || "—"} newcomerCount={newcomerCount} sponsorCount={sponsorCount} />
      <div className="feed-layout">
        <FilterRail filters={filters} setFilters={setFilters} counts={counts} />
        <main style={{ minWidth: 0 }}>
          <div className="feed-bar">
            <span className="count">{visibleCount}</span>
            <span className="sub">role{visibleCount !== 1 ? "s" : ""} match your filters</span>
            <div className="right">
              <div className="sort-tabs">
                <button className={"sort-tab" + (sort === "match" ? " active" : "")} onClick={() => setSort("match")}>Best match</button>
                <button className={"sort-tab" + (sort === "trust" ? " active" : "")} onClick={() => setSort("trust")}>Trust</button>
                <button className={"sort-tab" + (sort === "fresh" ? " active" : "")} onClick={() => setSort("fresh")}>Freshness</button>
              </div>
              <button className="btn btn-sm btn-ghost" onClick={() => setCompact(c => !c)}>
                {compact ? "☰ Detailed" : "☷ Compact"}
              </button>
            </div>
          </div>

          {loading ? (
            <div className="empty"><h3>Loading verified postings…</h3><p>Pulling from the pipeline.</p></div>
          ) : error ? (
            <div className="empty">
              <h3>Something went wrong</h3>
              <p>{error}</p>
              <button className="btn btn-sm" style={{ marginTop: 12 }} onClick={fetchPostings}>
                <Icon name="refresh" size={13} /> Try again
              </button>
            </div>
          ) : (
            <div className={"feed-list" + (compact ? " compact" : "")}>
              {filtered.length === 0 ? (
                <div className="empty"><h3>No matches</h3><p>Try widening your trust threshold or clearing filters.</p></div>
              ) : filtered.map(p => (
                <PostingCard
                  key={p.id}
                  p={p}
                  saved={!!saved[p.id]}
                  voted={votes[p.id] || null}
                  dismissed={!!dismissed[p.id]}
                  compact={compact}
                  onSave={id => setSaved(s => ({ ...s, [id]: !s[id] }))}
                  onVote={handleVote}
                  onDismiss={id => setDismissed(d => ({ ...d, [id]: true }))}
                />
              ))}
            </div>
          )}

          <div className="feed-foot">
            Showing {visibleCount} of {postings.length} verified postings · Refresh runs every 4 hours
          </div>
        </main>
      </div>
    </>
  );
}
