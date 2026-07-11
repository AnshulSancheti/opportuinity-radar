import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { Article, Hackathon, Job, Paginated, Stats } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Badge } from "@/components/Badge";
import { ArticleThumbnail } from "@/components/ArticleThumbnail";
import { ErrorState } from "@/components/States";

export default async function HomePage() {
  let stats: Stats | null = null;
  let news: Paginated<Article> | null = null;
  let jobs: Paginated<Job> | null = null;
  let hacks: Paginated<Hackathon> | null = null;
  let error = false;

  try {
    [stats, news, jobs, hacks] = await Promise.all([
      apiGet<Stats>("/admin/stats"),
      apiGet<Paginated<Article>>("/news?limit=5"),
      apiGet<Paginated<Job>>("/jobs?limit=5"),
      apiGet<Paginated<Hackathon>>("/hackathons?limit=5"),
    ]);
  } catch {
    error = true;
  }

  if (error) {
    return (
      <>
        <PageHeader title="Dashboard" subtitle="System status" />
        <ErrorState message="API unavailable — start backend with ./start.sh" />
      </>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader title="Dashboard" subtitle="Jobs, news, and hackathons at a glance" />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Jobs" value={stats?.total_jobs ?? 0} accent />
        <StatCard label="Articles" value={stats?.total_articles ?? 0} />
        <StatCard label="Hackathons" value={stats?.total_hackathons ?? 0} />
        <StatCard label="Source Failures" value={stats?.failed_sources ?? 0} />
      </div>

      <div className="valorant-card flex flex-wrap items-center justify-between gap-3 p-4 text-sm">
        <div className="text-[var(--valorant-muted)]">
          Last scrape:{" "}
          <span className="text-white">
            {stats?.last_scrape_at ? new Date(stats.last_scrape_at).toLocaleString() : "Never"}
          </span>
          {(stats?.active_scrapes?.length ?? 0) > 0 && (
            <span className="ml-3 text-[var(--valorant-cyan)]">
              Running: {stats!.active_scrapes.join(", ")}
            </span>
          )}
        </div>
        <Link
          href="/admin"
          className="valorant-btn border border-[var(--valorant-border)] px-3 py-1.5 text-xs uppercase tracking-wider text-[var(--valorant-red)] hover:border-[var(--valorant-red)]"
        >
          Admin →
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <FeedSection title="Latest News" href="/news" items={news?.items ?? []} render={(a: Article) => (
          <li key={a.id} className="border-b border-[var(--valorant-border)] py-2 last:border-0">
            <div className="flex gap-3">
              <ArticleThumbnail imageUrl={a.image_url} sourceName={a.source_name} title={a.title} />
              <div className="min-w-0 flex-1">
                <a href={a.url ?? "#"} target="_blank" rel="noreferrer" className="text-sm text-white hover:text-[var(--valorant-red)]">
                  {a.title}
                </a>
                <div className="mt-1 flex gap-2">
                  <Badge variant="muted">{a.source_name}</Badge>
                  <Badge>{a.category}</Badge>
                </div>
              </div>
            </div>
          </li>
        )} />
        <FeedSection title="Latest Jobs" href="/jobs" items={jobs?.items ?? []} render={(j: Job) => (
          <li key={j.id} className="border-b border-[var(--valorant-border)] py-2 last:border-0">
            <p className="text-sm font-medium text-white">{j.title}</p>
            <p className="text-xs text-[var(--valorant-muted)]">{j.company} · {j.location ?? "Remote"}</p>
          </li>
        )} />
        <FeedSection title="Hackathons" href="/hackathons" items={hacks?.items ?? []} render={(h: Hackathon) => (
          <li key={h.id} className="border-b border-[var(--valorant-border)] py-2 last:border-0">
            <p className="text-sm font-medium text-white">{h.name}</p>
            <p className="text-xs text-[var(--valorant-muted)]">{h.organizer ?? h.mode}</p>
          </li>
        )} />
      </div>
    </div>
  );
}

function FeedSection<T>({ title, href, items, render }: { title: string; href: string; items: T[]; render: (item: T) => React.ReactNode }) {
  return (
    <section className="valorant-card p-4">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-valorant text-sm font-bold tracking-widest text-[var(--valorant-red)]">{title}</h2>
        <Link href={href} className="text-xs uppercase tracking-wider text-[var(--valorant-muted)] hover:text-white">
          View all →
        </Link>
      </div>
      {items.length === 0 ? (
        <p className="text-xs text-[var(--valorant-muted)]">No data — run scrapers</p>
      ) : (
        <ul>{items.map(render)}</ul>
      )}
    </section>
  );
}
