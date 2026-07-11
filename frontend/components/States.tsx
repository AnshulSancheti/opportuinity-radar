export function EmptyState({ message }: { message: string }) {
  return (
    <div className="valorant-card p-8 text-center">
      <p className="font-valorant text-lg text-[var(--valorant-muted)]">{message}</p>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="border border-[var(--valorant-red)]/50 bg-[var(--valorant-red)]/10 p-4"
      style={{ clipPath: "polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)" }}>
      <p className="font-valorant text-sm text-[var(--valorant-red)]">⚠ {message}</p>
    </div>
  );
}

export function LoadingState() {
  return (
    <div className="flex items-center gap-3 p-8">
      <div className="h-3 w-3 animate-pulse rounded-full bg-[var(--valorant-red)]" />
      <p className="font-valorant text-sm tracking-widest text-[var(--valorant-muted)]">Loading…</p>
    </div>
  );
}
