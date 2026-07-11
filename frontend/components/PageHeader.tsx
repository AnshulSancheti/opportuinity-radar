export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-8">
      <div className="mb-2 flex items-center gap-3">
        <div className="h-8 w-1 bg-[var(--valorant-red)]" />
        <h1 className="font-valorant text-3xl font-bold text-white md:text-4xl">{title}</h1>
      </div>
      {subtitle && <p className="ml-4 text-sm text-[var(--valorant-muted)]">{subtitle}</p>}
      <div className="valorant-divider mt-4 max-w-xs" />
    </div>
  );
}
