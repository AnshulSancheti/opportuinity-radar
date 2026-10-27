"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { apiGet, apiPost, ApiError } from "@/lib/api";
import type { UserAction } from "@/lib/types";

type Account = { id: string; name: string; email: string };
type Auth = { user: Account | null; loading: boolean; error: string; actions: UserAction[]; refresh: () => Promise<void>; refreshActions: () => Promise<void>; logout: () => Promise<void> };
const Context = createContext<Auth | null>(null);
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actions, setActions] = useState<UserAction[]>([]);
  const refreshActions = useCallback(async () => {
    try { setActions(await apiGet<UserAction[]>("/actions")); }
    catch (e) { setActions([]); if (e instanceof ApiError && e.status === 401) setUser(null); throw e; }
  }, []);
  const refresh = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const account = await apiGet<Account>("/auth/me");
      setUser(account);
      await refreshActions();
    } catch (e) {
      setUser(null); setActions([]);
      if (!(e instanceof ApiError && e.status === 401)) setError("Could not connect to your account. Please retry.");
    } finally { setLoading(false); }
  }, [refreshActions]);
  useEffect(() => { void refresh(); }, [refresh]);
  const logout = async () => {
    await apiPost("/auth/logout", {});
    setUser(null); setActions([]);
  };
  return <Context.Provider value={{ user, loading, error, actions, refresh, refreshActions, logout }}>{children}</Context.Provider>;
}
export function useAuth() { const auth = useContext(Context); if (!auth) throw new Error("AuthProvider missing"); return auth; }
