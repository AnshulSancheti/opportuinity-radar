"use client";

import { apiPost } from "@/lib/api";

export function ActionButtons({
  itemType,
  itemId,
}: {
  itemType: "article" | "job" | "hackathon";
  itemId: number;
}) {
  const save = async (action: string) => {
    try {
      await apiPost("/actions", { item_type: itemType, item_id: itemId, action });
    } catch {
      /* silent */
    }
  };

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      <button onClick={() => save("saved")} className="valorant-btn-primary text-xs">
        Save
      </button>
      <button onClick={() => save("hidden")} className="valorant-btn-ghost text-xs">
        Dismiss
      </button>
      {itemType === "job" && (
        <button onClick={() => save("applied")} className="valorant-btn-ghost border-green-600/50 text-green-400 text-xs hover:border-green-400">
          Applied
        </button>
      )}
    </div>
  );
}
