"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { useState } from "react";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/news", label: "News" },
  { href: "/hackathons", label: "Hackathons" },
  { href: "/saved", label: "Saved" },
  { href: "/applied", label: "Applied" },
  { href: "/admin", label: "Admin" },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const signOut = async () => {
    setBusy(true); setError("");
    try { await logout(); router.push("/"); router.refresh(); }
    catch { setError("Sign out failed. Please retry."); }
    finally { setBusy(false); }
  };

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--valorant-border)] bg-[#0a1219]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="group flex items-center gap-3">
          <div
            className="flex h-9 w-9 items-center justify-center border border-[var(--valorant-red)] bg-[var(--valorant-red)]/10"
            style={{ clipPath: "polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px)" }}
          >
            <span className="font-valorant text-lg font-bold text-[var(--valorant-red)]">R</span>
          </div>
          <div>
            <p className="font-valorant text-lg font-bold leading-none tracking-widest text-white">RADAR</p>
            <p className="text-[10px] uppercase tracking-[0.3em] text-[var(--valorant-muted)]">Opportunity Radar</p>
          </div>
        </Link>
        <nav className="flex flex-wrap gap-1">
          {links.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`valorant-btn px-3 py-1.5 text-xs ${
                  active
                    ? "bg-[var(--valorant-red)] text-white"
                    : "border border-[var(--valorant-border)] bg-transparent text-[var(--valorant-muted)] hover:border-[var(--valorant-red)] hover:text-[var(--valorant-red)]"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
          {loading ? <span className="p-2 text-xs">Loading account…</span> : user ? <>
            <span className="p-2 text-xs text-white">{user.name}</span>
            <button disabled={busy} onClick={signOut} className="valorant-btn-ghost text-xs">{busy ? "Signing out…" : "Sign out"}</button>
          </> : <Link href="/login" className="valorant-btn-primary text-xs">Sign in / Create account</Link>}
          {error && <span role="alert" className="text-xs text-red-400">{error}</span>}
        </nav>
      </div>
      <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-[var(--valorant-red)] to-transparent opacity-60" />
    </header>
  );
}
