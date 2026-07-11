import { apiGet } from "@/lib/api";
import type { Job, Paginated } from "@/lib/types";
import { ActionButtons } from "@/components/ActionButtons";
import { EMPLOYMENT_OPTIONS, FilterSelect, LoadMoreLink, REMOTE_OPTIONS } from "@/components/FilterBar";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { EmptyState, ErrorState } from "@/components/States";

const PAGE_SIZE = 50;

export default async function JobsPage({
  searchParams,
}: {
  searchParams: {
    q?: string;
    skill?: string;
    company?: string;
    location?: string;
    remote_type?: string;
    employment_type?: string;
    offset?: string;
  };
}) {
  const offset = Math.max(0, parseInt(searchParams.offset || "0", 10) || 0);
  const params = new URLSearchParams();
  if (searchParams.q) params.set("q", searchParams.q);
  if (searchParams.skill) params.set("skill", searchParams.skill);
  if (searchParams.company) params.set("company", searchParams.company);
  if (searchParams.location) params.set("location", searchParams.location);
  if (searchParams.remote_type) params.set("remote_type", searchParams.remote_type);
  if (searchParams.employment_type) params.set("employment_type", searchParams.employment_type);
  params.set("limit", String(PAGE_SIZE));
  params.set("offset", String(offset));

  let data: Paginated<Job> | null = null;
  let error = false;
  try {
    data = await apiGet<Paginated<Job>>(`/jobs?${params}`);
  } catch {
    error = true;
  }

  const nextParams = new URLSearchParams(params);
  nextParams.set("offset", String(offset + PAGE_SIZE));
  const hasMore = data ? offset + data.items.length < data.total : false;

  return (
    <div className="space-y-6">
      <PageHeader title="Jobs" subtitle={`${data?.total ?? 0} active jobs`} />

      <form className="valorant-card grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
        <input name="q" placeholder="Search (e.g. internship)" defaultValue={searchParams.q} className="valorant-input" />
        <FilterSelect name="remote_type" label="Remote" options={REMOTE_OPTIONS} defaultValue={searchParams.remote_type} />
        <FilterSelect name="employment_type" label="Type" options={EMPLOYMENT_OPTIONS} defaultValue={searchParams.employment_type} />
        <input name="skill" placeholder="Skill (Python)" defaultValue={searchParams.skill} className="valorant-input" />
        <input name="company" placeholder="Company" defaultValue={searchParams.company} className="valorant-input" />
        <input name="location" placeholder="Location" defaultValue={searchParams.location} className="valorant-input" />
        <button type="submit" className="valorant-btn-primary sm:col-span-2 lg:col-span-1">Filter</button>
      </form>

      {error && <ErrorState message="Failed to load jobs" />}
      {!error && data?.items.length === 0 && <EmptyState message="No jobs — run jobs scraper" />}

      <div className="grid gap-4">
        {data?.items.map((j) => (
          <article key={j.id} className="valorant-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="font-valorant text-xl font-semibold text-white">{j.title}</h2>
                <p className="mt-1 text-sm text-[var(--valorant-muted)]">
                  {j.company} · {j.location ?? "Location N/A"}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {j.remote_type && <Badge variant="cyan">{j.remote_type}</Badge>}
                  {j.employment_type && <Badge variant="muted">{j.employment_type}</Badge>}
                  <Badge variant="muted">{j.source_name}</Badge>
                </div>
                {j.skills.length > 0 && (
                  <p className="mt-3 text-xs text-[var(--valorant-muted)]">
                    {j.skills.map((s) => (
                      <span key={s} className="mr-2 text-[var(--valorant-cyan)]">#{s}</span>
                    ))}
                  </p>
                )}
              </div>
              {j.apply_url && (
                <a href={j.apply_url} target="_blank" rel="noreferrer" className="valorant-btn-primary shrink-0">
                  Apply
                </a>
              )}
            </div>
            <ActionButtons itemType="job" itemId={j.id} />
          </article>
        ))}
      </div>

      <LoadMoreLink href={`/jobs?${nextParams}`} hasMore={hasMore} />
    </div>
  );
}
