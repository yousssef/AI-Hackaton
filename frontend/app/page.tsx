"use client";

import { useEffect, useState, useCallback } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://ai-hackatonn-production.up.railway.app";

interface Posting {
  id: number;
  company: string;
  title: string;
  description: string;
  location_raw: string;
  remote_type: string;
  role_family: string;
  posted_at: string;
  trust_score: number;
  genuinely_remote: boolean;
  scam_likelihood: number;
  newcomer_friendly_signals: string[];
  rationale: string;
  source_url: string;
  seniority: string;
}

const ROLE_FAMILIES = ["all", "engineering", "design", "marketing", "product", "data", "finance", "hr", "sales", "support"];

const trustColor = (score: number) => {
  if (score >= 85) return "bg-emerald-100 text-emerald-800 border-emerald-200";
  if (score >= 70) return "bg-yellow-100 text-yellow-800 border-yellow-200";
  return "bg-red-100 text-red-800 border-red-200";
};

function TrustBadge({ score }: { score: number }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${trustColor(score)}`}>
      {score >= 85 ? "✓" : score >= 70 ? "~" : "!"} Trust {score}
    </span>
  );
}

function PostingCard({ posting, onFeedback }: { posting: Posting; onFeedback: (id: number, signal: "up" | "down") => void }) {
  const [expanded, setExpanded] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState<"up" | "down" | null>(null);

  const daysAgo = posting.posted_at
    ? Math.floor((Date.now() - new Date(posting.posted_at).getTime()) / 86400000)
    : null;

  const handleFeedback = (signal: "up" | "down") => {
    setFeedbackGiven(signal);
    onFeedback(posting.id, signal);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{posting.role_family}</span>
            {daysAgo !== null && (
              <span className="text-xs text-gray-400">{daysAgo === 0 ? "Today" : `${daysAgo}d ago`}</span>
            )}
          </div>
          <h3 className="text-base font-semibold text-gray-900">{posting.title}</h3>
          <p className="text-sm text-gray-600 mt-0.5">{posting.company}</p>
          {posting.location_raw && <p className="text-xs text-gray-400 mt-0.5">📍 {posting.location_raw}</p>}
        </div>
        <TrustBadge score={posting.trust_score} />
      </div>

      <div className="flex flex-wrap gap-1.5 mt-3">
        {posting.genuinely_remote && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-200">
            🌍 Verified Remote
          </span>
        )}
        {posting.seniority && posting.seniority !== "any" && (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 border border-gray-200 capitalize">
            {posting.seniority}
          </span>
        )}
        {posting.newcomer_friendly_signals?.length > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">
            🤝 Newcomer Friendly
          </span>
        )}
      </div>

      <p className="mt-3 text-xs text-gray-500 italic border-l-2 border-gray-200 pl-2">{posting.rationale}</p>

      {posting.newcomer_friendly_signals?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {posting.newcomer_friendly_signals.map((s, i) => (
            <span key={i} className="text-xs bg-purple-50 text-purple-700 px-1.5 py-0.5 rounded">{s}</span>
          ))}
        </div>
      )}

      {expanded && (
        <div className="mt-3 text-sm text-gray-700 leading-relaxed border-t border-gray-100 pt-3 whitespace-pre-line">
          {posting.description}
        </div>
      )}

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
        <button onClick={() => setExpanded(!expanded)} className="text-xs text-gray-500 hover:text-gray-700 underline">
          {expanded ? "Show less" : "Show more"}
        </button>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleFeedback("up")}
            className={`text-sm px-2 py-1 rounded hover:bg-gray-100 transition-colors ${feedbackGiven === "up" ? "text-emerald-600 font-bold" : "text-gray-400"}`}
          >👍</button>
          <button
            onClick={() => handleFeedback("down")}
            className={`text-sm px-2 py-1 rounded hover:bg-gray-100 transition-colors ${feedbackGiven === "down" ? "text-red-500 font-bold" : "text-gray-400"}`}
          >👎</button>
          <a
            href={posting.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
          >
            Apply →
          </a>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [postings, setPostings] = useState<Posting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [roleFamily, setRoleFamily] = useState("all");
  const [days, setDays] = useState(14);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const fetchPostings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ days: String(days), limit: "50" });
      if (roleFamily !== "all") params.set("role_family", roleFamily);
      const res = await fetch(`${API_BASE}/api/postings?${params}`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      setPostings(await res.json());
      setLastRefreshed(new Date());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load postings");
    } finally {
      setLoading(false);
    }
  }, [roleFamily, days]);

  useEffect(() => { fetchPostings(); }, [fetchPostings]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch(`${API_BASE}/api/refresh`, { method: "POST" });
      await fetchPostings();
    } finally {
      setRefreshing(false);
    }
  };

  const handleFeedback = async (id: number, signal: "up" | "down") => {
    await fetch(`${API_BASE}/api/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ posting_id: id, signal }),
    }).catch(console.error);
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-bold text-gray-900">🌐 Scale Without Borders — Verified Remote Jobs</h1>
            <p className="text-xs text-gray-500 mt-0.5">AI-verified remote opportunities for newcomers to Canada</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>
            <a
              href={`${API_BASE}/api/export/csv?days=${days}`}
              target="_blank"
              className="text-xs bg-emerald-50 hover:bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-lg font-medium transition-colors border border-emerald-200"
            >
              ↓ Export CSV
            </a>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <div className="flex gap-1 flex-wrap">
            {ROLE_FAMILIES.map((rf) => (
              <button
                key={rf}
                onClick={() => setRoleFamily(rf)}
                className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors border ${roleFamily === rf ? "bg-blue-600 text-white border-blue-600" : "bg-white text-gray-600 border-gray-200 hover:border-blue-300"
                  }`}
              >
                {rf.charAt(0).toUpperCase() + rf.slice(1)}
              </button>
            ))}
          </div>
          <div className="ml-auto flex gap-2">
            {[7, 14].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`text-xs px-3 py-1.5 rounded-full font-medium border transition-colors ${days === d ? "bg-gray-800 text-white border-gray-800" : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
                  }`}
              >
                Last {d} days
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-gray-600">{loading ? "Loading..." : `${postings.length} verified remote postings`}</p>
          {lastRefreshed && <p className="text-xs text-gray-400">Updated {lastRefreshed.toLocaleTimeString()}</p>}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-sm text-red-700">
            {error} — make sure the backend is running on port 8000.
          </div>
        )}

        {loading ? (
          <div className="grid gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
                <div className="h-5 bg-gray-200 rounded w-3/4 mb-1" />
                <div className="h-4 bg-gray-200 rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : postings.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <p className="text-4xl mb-3">🔍</p>
            <p className="font-medium">No verified postings found.</p>
            <p className="text-sm mt-1">Try a different filter or click Refresh to run the pipeline.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {postings.map((p) => <PostingCard key={p.id} posting={p} onFeedback={handleFeedback} />)}
          </div>
        )}

        <footer className="mt-10 pt-6 border-t border-gray-200 text-center text-xs text-gray-400">
          Powered by Claude AI · We Work Remotely · Scale Without Borders Canada
        </footer>
      </div>
    </main>
  );
}
