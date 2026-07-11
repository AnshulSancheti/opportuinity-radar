import { apiGet } from "@/lib/api";
import type { Hackathon, Paginated } from "@/lib/types";
import { ActionButtons } from "@/components/ActionButtons";
import { FilterSelect, LoadMoreLink, MODE_OPTIONS } from "@/components/FilterBar";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { EmptyState, ErrorState } from "@/components/States";

const PAGE_SIZE = 50;

export default async function HackathonsPage({
  searchParams,
}: {
  searchParams: { q?: string; mode?: string; offset?: string };
}) {
  const offset = Math.max(0, parseInt(searchParams.offset || "0", 10) || 0);
  const params = new URLSearchParams();
  if (searchParams.q) params.set("q", searchParams.q);
  if (searchParams.mode) params.set("mode", searchParams.mode);
  params.set("limit", String(PAGE_SIZE));
  params.set("offset", String(offset));

  let data: Paginated<Hackathon> | null = null;
  let error = false;
  try {
    data = await apiGet<Paginated<Hackathon>>(`/hackathons?${params}`);
  } catch {
    error = true;
  }

  const nextParams = new URLSearchParams(params);
  nextParams.set("offset", String(offset + PAGE_SIZE));
  const hasMore = data ? offset + data.items.length < data.total : false;

  return (
    <div className="space-y-6">
      <PageHeader title="Hackathons" subtitle={`${data?.total ?? 0} upcoming hackathons`} />

      <form className="valorant-card flex flex-wrap items-end gap-3 p-4">
        <label className="flex flex-col gap-1 text-xs uppercase tracking-wider text-[var(--valorant-muted)]">
          Search
          <input name="q" placeholder="Name or organizer" defaultValue={searchParams.q} className="valorant-input min-w-[200px]" />
        </label>
        <FilterSelect name="mode" label="Format" options={MODE_OPTIONS} defaultValue={searchParams.mode} />
        <button type="submit" className="valorant-btn-primary">Filter</button>
      </form>

      {error && <ErrorState message="Failed to load hackathons" />}
      {!error && data?.items.length === 0 && <EmptyState message="No hackathons — run hackathons scraper" />}

      <div className="grid gap-4 md:grid-cols-2">
        {data?.items.map((h) => (
          <article key={h.id} className="valorant-card p-5">
            <h2 className="font-valorant text-xl font-semibold text-white">{h.name}</h2>
            <p className="mt-1 text-sm text-[var(--valorant-muted)]">{h.organizer ?? "Unknown org"}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {h.mode && <Badge variant="cyan">{h.mode}</Badge>}
              {h.location && <Badge variant="muted">{h.location}</Badge>}
            </div>
            {h.registration_deadline && (
              <p className="mt-3 font-valorant text-xs tracking-wider text-[var(--valorant-red)]">
                Deadline: {new Date(h.registration_deadline).toLocaleDateString()}
              </p>
            )}
            {h.prize_text && <p className="mt-1 text-sm text-green-400">{h.prize_text}</p>}
            {h.url && (
              <a href={h.url} target="_blank" rel="noreferrer" className="valorant-btn-primary mt-4 inline-flex">
                Register
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
