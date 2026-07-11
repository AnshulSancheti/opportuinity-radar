export function Badge({ children, variant = "default" }: { children: React.ReactNode; variant?: "default" | "cyan" | "muted" }) {
  const styles = {
    default: "bg-[var(--valorant-red)]/15 text-[var(--valorant-red)] border-[var(--valorant-red)]/35",
    cyan: "bg-cyan-500/10 text-[var(--valorant-cyan)] border-cyan-500/30",
    muted: "bg-white/5 text-[var(--valorant-muted)] border-[var(--valorant-border)]",
  };
  return (
    <span className={`valorant-badge border ${styles[variant]}`}>{children}</span>
  );
}
