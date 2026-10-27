"use client";

import { useCallback, useEffect, useState } from "react";
import { API_URL } from "@/lib/api";
import type { ScrapeRun } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { useAuth } from "@/components/AuthProvider";
import Link from "next/link";
import { ErrorState } from "@/components/States";

const MODULES = [
  { id: "news", label: "News", hint: "RSS, HN, Dev.to" },
  { id: "hackathons", label: "Hackathons", hint: "Curated + MLH" },
] as const;

export default function AdminPage() {
  const { user, loading } = useAuth();
  const [password, setPassword] = useState("");
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [activeScrapes, setActiveScrapes] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  const authed = password.length >= 4;

  const loadRuns = useCallback(async () => {
    if (!authed) return;
    try {
      const res = await fetch(`${API_URL}/admin/scrape-runs`, {
        credentials: "include",
        headers: { "X-Admin-Password": password },
        cache: "no-store",
      });
      if (!res.ok) { const data = await res.json().catch(() => ({})); throw new Error(data.detail || "Unable to load runs"); }
      setRuns(await res.json());
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load runs");
      setRuns([]);
    }
  }, [authed, password]);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/admin/stats`, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      setActiveScrapes(data.active_scrapes ?? []);
    } catch {
      // stats optional when API down
    }
  }, []);

  useEffect(() => {
    if (!authed) return;
    loadRuns();
    loadStatus();
    const id = setInterval(() => {
      loadRuns();
      loadStatus();
    }, 5000);
    return () => clearInterval(id);
  }, [authed, loadRuns, loadStatus]);

  const runScraper = async (module: string) => {
    setBusy(module);
    setMessage("");
    try {
      const res = await fetch(`${API_URL}/admin/run-scraper`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Password": password,
        },
        body: JSON.stringify({ module }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409) {
        setMessage(`${module} scrape already running`);
      } else if (!res.ok) {
        throw new Error(data.detail ?? "Failed to start scraper");
      } else {
        setMessage(`Started ${module} scrape — refresh runs below as it completes`);
        setActiveScrapes((prev) => Array.from(new Set([...prev, module])));
      }
      await loadRuns();
      await loadStatus();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Scrape failed to start");
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <p>Loading account…</p>;
  if (!user) return <Link href="/login" className="valorant-btn-primary">Sign in to access admin controls</Link>;

  return (
    <div className="space-y-6">
      <PageHeader title="Admin" subtitle="Scraper operations and run history" />

      <div className="valorant-card p-4">
        <label className="mb-2 block text-xs uppercase tracking-widest text-[var(--valorant-muted)]">
          Admin passphrase
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="From ADMIN_PASSWORD in .env"
          className="valorant-input max-w-sm"
        />
      </div>

      {error && <ErrorState message={error} />}

      {authed && !error && (
        <section className="valorant-card p-4">
          <h2 className="mb-4 font-valorant text-sm font-bold tracking-widest text-[var(--valorant-red)]">
            Run scrapers
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {MODULES.map((m) => {
              const running = activeScrapes.includes(m.id);
              return (
                <button
                  key={m.id}
                  type="button"
                  disabled={!!busy || running}
                  onClick={() => runScraper(m.id)}
                  className="valorant-btn border border-[var(--valorant-border)] p-4 text-left disabled:opacity-50"
                >
                  <p className="font-valorant text-sm tracking-widest text-white">{m.label}</p>
                  <p className="mt-1 text-xs text-[var(--valorant-muted)]">{m.hint}</p>
                  <p className="mt-2 text-xs uppercase tracking-wider text-[var(--valorant-red)]">
                    {running ? "Running…" : busy === m.id ? "Starting…" : "Run now"}
                  </p>
                </button>
              );
            })}
          </div>
          {message && <p className="mt-3 text-sm text-[var(--valorant-muted)]">{message}</p>}
          {activeScrapes.length > 0 && (
            <p className="mt-2 text-xs text-[var(--valorant-cyan)]">
              Active: {activeScrapes.join(", ")} — table auto-refreshes every 5s
            </p>
          )}
        </section>
      )}

      <div className="valorant-card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--valorant-border)] text-left font-valorant text-xs tracking-widest text-[var(--valorant-muted)]">
              <th className="p-3">Source</th>
              <th className="p-3">Module</th>
              <th className="p-3">Status</th>
              <th className="p-3">Found</th>
              <th className="p-3">Inserted</th>
              <th className="p-3">Started</th>
            </tr>
          </thead>
          <tbody>
            {runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-6 text-center text-[var(--valorant-muted)]">
                  {authed ? "No scrape runs yet — trigger a module above" : "Enter passphrase to view runs"}
                </td>
              </tr>
            ) : (
              runs.map((r) => (
                <tr key={r.id} className="border-b border-[var(--valorant-border)]/50 hover:bg-white/5">
                  <td className="p-3 text-white">{r.source_name}</td>
                  <td className="p-3">
                    <Badge variant="muted">{r.module}</Badge>
                  </td>
                  <td className="p-3">
                    <Badge variant={r.status === "success" ? "cyan" : r.status === "running" ? "default" : "default"}>
                      {r.status}
                    </Badge>
                  </td>
                  <td className="p-3">{r.items_found}</td>
                  <td className="p-3 text-[var(--valorant-red)]">{r.items_inserted}</td>
                  <td className="p-3 text-[var(--valorant-muted)]">{new Date(r.started_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
