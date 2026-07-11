import Link from "next/link";

type Option = { value: string; label: string };

export function FilterSelect({
  name,
  label,
  options,
  defaultValue = "",
}: {
  name: string;
  label: string;
  options: Option[];
  defaultValue?: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs uppercase tracking-wider text-[var(--valorant-muted)]">
      {label}
      <select name={name} defaultValue={defaultValue} className="valorant-input">
        {options.map((o) => (
          <option key={o.value || "all"} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function LoadMoreLink({
  href,
  hasMore,
}: {
  href: string;
  hasMore: boolean;
}) {
  if (!hasMore) return null;
  return (
    <div className="flex justify-center pt-4">
      <Link
        href={href}
        className="valorant-btn border border-[var(--valorant-border)] px-6 py-2 text-sm uppercase tracking-wider text-[var(--valorant-red)] hover:border-[var(--valorant-red)]"
      >
        Load more
      </Link>
    </div>
  );
}

export const NEWS_CATEGORIES = [
  "AI/ML",
  "Cybersecurity",
  "Startups",
  "Developer Tools",
  "Cloud",
  "Programming",
  "Data Science",
  "Other",
] as const;

export const REMOTE_OPTIONS = [
  { value: "", label: "All" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "Onsite" },
];

export const EMPLOYMENT_OPTIONS = [
  { value: "", label: "All" },
  { value: "internship", label: "Internship" },
  { value: "full-time", label: "Full-time" },
  { value: "part-time", label: "Part-time" },
  { value: "contract", label: "Contract" },
];

export const MODE_OPTIONS = [
  { value: "", label: "All" },
  { value: "online", label: "Online" },
  { value: "offline", label: "Offline" },
  { value: "hybrid", label: "Hybrid" },
];
