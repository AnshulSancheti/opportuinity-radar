"use client";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import type { UserAction } from "@/lib/types";

type Account = { id: string; name: string; email: string };
type Auth = { user: Account | null; loading: boolean; error: string; actions: UserAction[]; refresh: () => Promise<void>; refreshActions: () => Promise<void>; logout: () => Promise<void> };
const Context = createContext<Auth | null>(null);
async function readSession() {
  const user = await apiGet<Account>("/auth/me");
  const actions = await apiGet<UserAction[]>("/actions");
  return { user, actions };
}
const accountError = (error: unknown) => error instanceof ApiError && error.status === 401 ? "" : "Could not connect to your account. Please retry.";
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actions, setActions] = useState<UserAction[]>([]);
  const generation = useRef(0);
  const refreshActions = useCallback(async () => {
    const version = generation.current;
    try { const data = await apiGet<UserAction[]>("/actions"); if (version === generation.current) setActions(data); }
    catch (e) { if (version === generation.current) { setActions([]); if (e instanceof ApiError && e.status === 401) setUser(null); } throw e; }
  }, []);
  const refresh = useCallback(async () => {
    const version = ++generation.current;
    setLoading(true); setError("");
    try { const session = await readSession(); if (version === generation.current) { setUser(session.user); setActions(session.actions); } }
    catch (e) { if (version === generation.current) { setUser(null); setActions([]); setError(accountError(e)); } }
    finally { if (version === generation.current) setLoading(false); }
  }, []);
  useEffect(() => {
    let active = true;
    const version = generation.current;
    readSession().then(session => { if (active && version === generation.current) { setUser(session.user); setActions(session.actions); } })
      .catch(e => { if (active && version === generation.current) setError(accountError(e)); })
      .finally(() => { if (active && version === generation.current) setLoading(false); });
    return () => { active = false; };
  }, []);
  const logout = async () => {
    ++generation.current;
    await apiPost("/auth/logout", {});
    setUser(null); setActions([]); setLoading(false);
  };
  return <Context.Provider value={{ user, loading, error, actions, refresh, refreshActions, logout }}>{children}</Context.Provider>;
}
export function useAuth() { const auth = useContext(Context); if (!auth) throw new Error("AuthProvider missing"); return auth; }
