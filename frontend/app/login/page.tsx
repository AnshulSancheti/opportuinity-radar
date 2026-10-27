"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiPost } from "@/lib/api";
import { useAuth } from "@/components/AuthProvider";
import Link from "next/link";

export default function LoginPage() {
  const [register, setRegister] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { refresh, user } = useAuth();
  const router = useRouter();
  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setError(""); setBusy(true);
    const data = new FormData(event.currentTarget);
    try {
      await apiPost(`/auth/${register ? "register" : "login"}`, { email: data.get("email"), password: data.get("password"), ...(register ? { name: data.get("name") } : {}) });
      await refresh(); router.push("/saved"); router.refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Unable to sign in"); }
    finally { setBusy(false); }
  };
  return <section className="valorant-card mx-auto max-w-md space-y-5 p-6">
    <h1 className="font-valorant text-2xl text-white">{register ? "Create your account" : "Welcome back"}</h1>
    <p className="text-sm text-[var(--valorant-muted)]">Keep your articles, hackathons, and application tracker together.</p>
    {user ? <p>You’re signed in as {user.email}. <Link href="/saved" className="text-red-400">Open your saved items →</Link></p> : <>
    <form onSubmit={submit} className="space-y-4">
      {register && <label className="block text-sm">Name<input name="name" required maxLength={80} autoComplete="name" className="valorant-input mt-1 w-full" /></label>}
      <label className="block text-sm">Email<input name="email" type="email" required maxLength={254} autoComplete="email" className="valorant-input mt-1 w-full" /></label>
      <label className="block text-sm">Password<input name="password" type="password" required minLength={10} maxLength={128} autoComplete={register ? "new-password" : "current-password"} className="valorant-input mt-1 w-full" /></label>
      {register && <p className="text-xs text-[var(--valorant-muted)]">Use at least 10 characters.</p>}
      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      <button disabled={busy} className="valorant-btn-primary w-full disabled:opacity-50">{busy ? "Please wait…" : register ? "Create account" : "Sign in"}</button>
    </form>
    <button disabled={busy} onClick={() => { setRegister(!register); setError(""); }} className="text-sm text-[var(--valorant-cyan)]">{register ? "Already have an account? Sign in" : "New here? Create an account"}</button>
    </>}
  </section>;
}
