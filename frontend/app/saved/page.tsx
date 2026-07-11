import { apiGet } from "@/lib/api";
import type { UserAction } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";
import { EmptyState, ErrorState } from "@/components/States";

export default async function SavedPage() {
  let actions: UserAction[] = [];
  let error = false;
  try {
    actions = await apiGet<UserAction[]>("/actions/saved");
  } catch {
    error = true;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Saved" subtitle="Saved opportunities" />
      {error && <ErrorState message="Failed to load saved items" />}
      {actions.length === 0 && !error && <EmptyState message="No saved items yet" />}
      <div className="grid gap-3">
        {actions.map((a) => (
          <div key={a.id} className="valorant-card flex items-center justify-between p-4">
            <div>
              <Badge>{a.item_type}</Badge>
              <span className="ml-3 text-sm text-white">#{a.item_id}</span>
            </div>
            <span className="text-xs text-[var(--valorant-muted)]">
              {new Date(a.created_at).toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
