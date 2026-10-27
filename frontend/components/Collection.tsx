"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { apiGet } from "@/lib/api";
import { ActionButtons } from "@/components/ActionButtons";
import { PageHeader } from "@/components/PageHeader";

type Item = { id: number; item_id: number; item_type: "article" | "hackathon"; title: string; subtitle: string | null; url: string | null; deadline: string | null; created_at: string; status: string | null; source_name: string; end_date: string | null };
export function Collection({ applied = false }: { applied?: boolean }) {
  const { user, loading, error: accountError, refresh } = useAuth();
  const [items, setItems] = useState<Item[]>([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(true);
  const load = useCallback(async () => {
    if (!user) { setItems([]); setBusy(false); return; }
    setBusy(true); setError("");
    try { setItems(await apiGet<Item[]>(`/actions/saved?action=${applied ? "applied" : "saved"}`)); }
    catch (e) { setItems([]); setError(e instanceof Error ? e.message : "Could not load collection"); }
    finally { setBusy(false); }
  }, [user, applied]);
  useEffect(() => { void load(); }, [load]);
  const shown = items.filter(i => filter === "all" || i.item_type === filter);
  return <div className="space-y-6">
    <PageHeader title={applied ? "Applied hackathons" : "Your saved items"} subtitle={applied ? "Your record of applications submitted on organizers’ websites" : "Articles and hackathons saved to your account"} />
    {loading ? <p role="status">Loading account…</p> : !user ? <div className="valorant-card p-6">{accountError ? <><p role="alert">{accountError}</p><button onClick={() => void refresh()} className="valorant-btn-primary mt-3">Retry</button></> : <><p>Sign in to view your private collection.</p><Link href="/login" className="valorant-btn-primary mt-3 inline-flex">Sign in / Create account</Link></>}</div> : <>
      {!applied && <label className="block text-sm">Show <select value={filter} onChange={e => setFilter(e.target.value)} className="valorant-input ml-2"><option value="all">All saved items</option><option value="article">Articles</option><option value="hackathon">Hackathons</option></select></label>}
      {busy && <p role="status">Loading collection…</p>}
      {error && <div role="alert"><p className="text-red-400">{error}</p><button onClick={() => void load()} className="valorant-btn-ghost mt-2">Retry</button></div>}
      {!busy && !error && shown.length === 0 && <div className="valorant-card p-6"><p>{applied ? "No hackathons marked applied yet." : "No saved items in this collection yet."}</p><Link href={applied || filter === "hackathon" ? "/hackathons" : "/news"} className="mt-3 inline-block text-[var(--valorant-cyan)]">Discover {applied || filter === "hackathon" ? "hackathons" : "articles"} →</Link></div>}
      <div className="grid gap-4 md:grid-cols-2">{shown.map(item => <article key={item.id} className="valorant-card p-5">
        <p className="text-xs uppercase text-[var(--valorant-cyan)]">{item.item_type === "article" ? "Article" : "Hackathon"}</p>
        <h2 className="mt-2 text-xl font-semibold text-white">{item.title}</h2>
        <p className="mt-1 text-sm text-[var(--valorant-muted)]">{item.subtitle}</p>
        {item.item_type === "hackathon" && (item.status !== "active" || (item.end_date && new Date(item.end_date).getTime() < Date.now())) && <p className="mt-2 text-xs text-amber-300">{item.source_name === "static_list" ? "Legacy listing · details unverified" : item.status === "expired" || (item.end_date && new Date(item.end_date).getTime() < Date.now()) ? "This event has ended" : "No longer listed by the source"} · retained in your collection</p>}
        {item.deadline && <p className="mt-2 text-xs">Registration deadline: {new Date(item.deadline).toLocaleDateString()}</p>}
        <p className="mt-2 text-xs">{applied ? "Marked applied" : "Saved"}: {new Date(item.created_at).toLocaleDateString()}</p>
        {item.url && <a href={item.url} target="_blank" rel="noreferrer" className="mt-3 inline-block text-[var(--valorant-cyan)]">{item.item_type === "article" ? "Read article" : "Open hackathon"} ↗</a>}
        <ActionButtons itemType={item.item_type} itemId={item.item_id} onChange={() => void load()} />
      </article>)}</div>
    </>}
  </div>;
}
