import { apiGet } from "@/lib/api";
import type { Article, Paginated } from "@/lib/types";
import { ActionButtons } from "@/components/ActionButtons";
import { ArticleThumbnail } from "@/components/ArticleThumbnail";
import { FilterSelect, LoadMoreLink, NEWS_CATEGORIES } from "@/components/FilterBar";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { EmptyState, ErrorState } from "@/components/States";

const PAGE_SIZE = 50;

const CATEGORY_OPTIONS = [
  { value: "", label: "All categories" },
  ...NEWS_CATEGORIES.map((c) => ({ value: c, label: c })),
];

export default async function NewsPage({
  searchParams,
}: {
  searchParams: { q?: string; category?: string; source?: string; offset?: string };
}) {
  const offset = Math.max(0, parseInt(searchParams.offset || "0", 10) || 0);
  const params = new URLSearchParams();
  if (searchParams.q) params.set("q", searchParams.q);
  if (searchParams.category) params.set("category", searchParams.category);
  if (searchParams.source) params.set("source", searchParams.source);
  params.set("limit", String(PAGE_SIZE));
  params.set("offset", String(offset));

  let data: Paginated<Article> | null = null;
  let error = false;
  try {
    data = await apiGet<Paginated<Article>>(`/news?${params}`);
  } catch {
    error = true;
  }

  const nextParams = new URLSearchParams(params);
  nextParams.set("offset", String(offset + PAGE_SIZE));
  const hasMore = data ? offset + data.items.length < data.total : false;

  return (
    <div className="space-y-6">
      <PageHeader title="News" subtitle={`${data?.total ?? 0} articles in database`} />

      <form className="valorant-card flex flex-wrap items-end gap-3 p-4">
        <label className="flex flex-col gap-1 text-xs uppercase tracking-wider text-[var(--valorant-muted)]">
          Search
          <input name="q" placeholder="Search news..." defaultValue={searchParams.q} className="valorant-input min-w-[200px]" />
        </label>
        <FilterSelect name="category" label="Category" options={CATEGORY_OPTIONS} defaultValue={searchParams.category} />
        <label className="flex flex-col gap-1 text-xs uppercase tracking-wider text-[var(--valorant-muted)]">
          Source
          <input name="source" placeholder="e.g. Dev.to" defaultValue={searchParams.source} className="valorant-input min-w-[160px]" />
        </label>
        <button type="submit" className="valorant-btn-primary">Search</button>
      </form>

      {error && <ErrorState message="Failed to load news" />}
      {!error && data?.items.length === 0 && <EmptyState message="No articles — run news scraper" />}

      <div className="grid gap-4">
        {data?.items.map((a) => (
          <article key={a.id} className="valorant-card p-5">
            <div className="flex gap-4">
              <ArticleThumbnail imageUrl={a.image_url} sourceName={a.source_name} title={a.title} />
              <div className="min-w-0 flex-1">
                <a href={a.url ?? "#"} target="_blank" rel="noreferrer"
                  className="font-valorant text-xl font-semibold text-white hover:text-[var(--valorant-red)]">
                  {a.title}
                </a>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Badge variant="muted">{a.source_name}</Badge>
                  <Badge>{a.category}</Badge>
                  {a.score != null && <Badge variant="cyan">↑ {a.score}</Badge>}
                </div>
                {a.summary && <p className="mt-3 text-sm leading-relaxed text-[var(--valorant-muted)] line-clamp-2">{a.summary}</p>}
                <ActionButtons itemType="article" itemId={a.id} />
              </div>
            </div>
          </article>
        ))}
      </div>

      <LoadMoreLink href={`/news?${nextParams}`} hasMore={hasMore} />
    </div>
  );
}
