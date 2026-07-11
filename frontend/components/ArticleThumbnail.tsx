export function ArticleThumbnail({
  imageUrl,
  sourceName,
  title,
}: {
  imageUrl: string | null;
  sourceName: string;
  title: string;
}) {
  const initial = (sourceName || "?").charAt(0).toUpperCase();

  return (
    <div
      className="relative h-24 w-32 shrink-0 overflow-hidden border border-[var(--valorant-red)]/40 bg-[var(--valorant-bg-elevated)]"
      style={{ clipPath: "polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)" }}
    >
      {imageUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={imageUrl} alt={title} className="h-full w-full object-cover" loading="lazy" />
      ) : (
        <div className="flex h-full w-full items-center justify-center">
          <span className="font-valorant text-2xl font-bold text-[var(--valorant-red)]">{initial}</span>
        </div>
      )}
    </div>
  );
}
