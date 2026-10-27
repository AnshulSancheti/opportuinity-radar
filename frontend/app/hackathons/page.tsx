"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useFeed } from "@/lib/useFeed";
import type { Hackathon, Paginated } from "@/lib/types";
import { ActionButtons } from "@/components/ActionButtons";
import { FilterSelect, LoadMoreLink, MODE_OPTIONS } from "@/components/FilterBar";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { EmptyState, ErrorState } from "@/components/States";

type SourceStatus = { sources: { name: string; last_success_at: string | null; status: string; count: number }[]; auto_refresh: boolean; refresh_hours: number };

const PAGE_SIZE = 50;

export default function HackathonsPage() {
  return <Suspense fallback={<p role="status">Loading hackathons…</p>}><HackathonsFeed /></Suspense>;
}
function HackathonsFeed() {
  const searchParams = Object.fromEntries(useSearchParams().entries());
  const offset = Math.max(0, parseInt(searchParams.offset || "0", 10) || 0);
  const params = new URLSearchParams();
  if (searchParams.q) params.set("q", searchParams.q);
  if (searchParams.source) params.set("source", searchParams.source);
  if (searchParams.mode) params.set("mode", searchParams.mode);
  params.set("limit", String(PAGE_SIZE));
  params.set("offset", String(offset));

  const { data, error, loading } = useFeed<Paginated<Hackathon>>(`/hackathons?${params}`);
  const { data: freshness } = useFeed<SourceStatus>("/hackathons/sources");

  const nextParams = new URLSearchParams(params);
  nextParams.set("offset", String(offset + PAGE_SIZE));
  const hasMore = data ? offset + data.items.length < data.total : false;

  return (
    <div className="space-y-6">
      <PageHeader title="Hackathons" subtitle={`${data?.total ?? 0} open or upcoming hackathons`} />

      {freshness && <section className="valorant-card space-y-2 p-4 text-sm" aria-label="Hackathon sources">
        <p className="text-white">Live listings from MLH and Devpost{freshness.auto_refresh ? ` · refreshes every ${freshness.refresh_hours} hours` : ""}</p>
        {freshness.sources.map(source => <p key={source.name} className="text-xs text-[var(--valorant-muted)]">
          {source.name === "mlh" ? "MLH" : "Devpost"}: {source.count} listings · {source.last_success_at ? `last fetched ${new Date(source.last_success_at).toLocaleString()}` : "awaiting first successful refresh"}
          {source.status === "failed" || source.status === "partial_failure" ? " · latest refresh failed; retrying automatically" : source.status === "running" ? " · refreshing…" : ""}
        </p>)}
        <p className="text-xs text-[var(--valorant-muted)]">Registration deadlines are shown only when provided. Devpost dates describe its submission window.</p>
      </section>}

      <form className="valorant-card flex flex-wrap items-end gap-3 p-4">
        <label className="flex flex-col gap-1 text-xs uppercase tracking-wider text-[var(--valorant-muted)]">
          Search
          <input name="q" placeholder="Name or organizer" defaultValue={searchParams.q} className="valorant-input min-w-[200px]" />
        </label>
        <FilterSelect name="mode" label="Format" options={MODE_OPTIONS} defaultValue={searchParams.mode} />
        <FilterSelect name="source" label="Source" options={[{ value: "", label: "All sources" }, { value: "mlh", label: "MLH" }, { value: "devpost", label: "Devpost" }]} defaultValue={searchParams.source} />
        <button type="submit" className="valorant-btn-primary">Filter</button>
      </form>

      {loading && <p role="status">Loading hackathons…</p>}
      {error && <ErrorState message="Failed to load hackathons" />}
      {!loading && !error && data?.items.length === 0 && <EmptyState message="No open or upcoming hackathons match these filters." />}

      <div className="grid gap-4 md:grid-cols-2">
        {data?.items.map((h) => (
          <article key={h.id} className="valorant-card p-5">
            <h2 className="font-valorant text-xl font-semibold text-white">{h.name}</h2>
            <p className="mt-1 text-sm text-[var(--valorant-muted)]">{h.organizer ?? (h.source_name === "mlh" ? "MLH member event" : "Organizer not listed")}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <a href={h.source_name === "mlh" ? "https://mlh.io/events" : "https://devpost.com/hackathons"} target="_blank" rel="noreferrer"><Badge>{h.source_name === "mlh" ? "MLH" : "Devpost"}</Badge></a>
              {h.mode && <Badge variant="cyan">{h.mode}</Badge>}
              {h.location && <Badge variant="muted">{h.location}</Badge>}
            </div>
            {h.start_date && <p className="mt-3 text-xs text-[var(--valorant-muted)]">
              {h.source_name === "devpost" ? "Submissions" : "Event"}: {new Date(h.start_date).toLocaleDateString("en-IN", { timeZone: "UTC" })}{h.end_date ? ` – ${new Date(h.end_date).toLocaleDateString("en-IN", { timeZone: "UTC" })}` : ""}
            </p>}
            {!h.start_date && h.end_date && <p className="mt-3 text-xs text-[var(--valorant-muted)]">{h.source_name === "devpost" ? "Submissions end" : "Event ends"}: {new Date(h.end_date).toLocaleDateString("en-IN", { timeZone: "UTC" })}</p>}
            {h.registration_deadline && (
              <p className="mt-3 font-valorant text-xs tracking-wider text-[var(--valorant-red)]">
                Deadline: {new Date(h.registration_deadline).toLocaleDateString()}
              </p>
            )}
            {h.prize_text && <p className="mt-1 text-sm text-green-400">{h.prize_text}</p>}
            {h.url && (
              <a href={h.url} target="_blank" rel="noreferrer" className="valorant-btn-primary mt-4 inline-flex">
                View hackathon ↗
              </a>
            )}
            <ActionButtons itemType="hackathon" itemId={h.id} />
          </article>
        ))}
      </div>

      <LoadMoreLink href={`/hackathons?${nextParams}`} hasMore={hasMore} />
    </div>
  );
}
