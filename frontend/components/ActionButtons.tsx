"use client";
import Link from "next/link";
import { useState } from "react";
import { apiDelete, apiPost } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";

export function ActionButtons({ itemType, itemId, onChange }: { itemType: "article" | "hackathon"; itemId: number; onChange?: () => void }) {
  const { user, loading, actions, refreshActions, error: accountError } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const has = (action: string) => actions.some(a => a.item_type === itemType && a.item_id === itemId && a.action === action);
  const toggle = async (action: "saved" | "applied") => {
    setBusy(true); setError("");
    try {
      if (has(action)) await apiDelete(`/actions?${new URLSearchParams({ item_type: itemType, item_id: String(itemId), action })}`);
      else await apiPost("/actions", { item_type: itemType, item_id: itemId, action });
      await refreshActions(); onChange?.();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not update item"); }
    finally { setBusy(false); }
  };
  if (loading) return <p className="mt-3 text-xs" role="status">Loading your saved status…</p>;
  if (!user) return <div className="mt-3 text-xs">{accountError && <p role="alert" className="text-red-400">{accountError}</p>}<Link href="/login" className="text-[var(--valorant-cyan)]">Sign in to save{itemType === "hackathon" ? " and track applications" : " this article"}</Link></div>;
  return <div className="mt-3 space-y-2">
    <div className="flex flex-wrap gap-2">
      <button aria-pressed={has("saved")} disabled={busy} onClick={() => toggle("saved")} className="valorant-btn-primary text-xs disabled:opacity-50">{has("saved") ? "Saved ✓ · Unsave" : "Save"}</button>
      {itemType === "hackathon" && <button aria-pressed={has("applied")} disabled={busy} onClick={() => toggle("applied")} className="valorant-btn-ghost text-xs disabled:opacity-50">{has("applied") ? "Applied ✓ · Undo" : "Mark applied"}</button>}
    </div>
    {busy && <p role="status" className="text-xs">Updating…</p>}
    {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
  </div>;
}
