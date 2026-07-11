export function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className={`valorant-stat ${accent ? "border-[var(--valorant-red)]/50" : ""}`}>
      <p className="font-valorant text-xs tracking-widest text-[var(--valorant-muted)]">{label}</p>
      <p className={`font-valorant mt-1 text-3xl font-bold ${accent ? "text-[var(--valorant-red)]" : "text-white"}`}>
        {value}
      </p>
    </div>
  );
}
