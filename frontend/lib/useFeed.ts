"use client";
import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
export function useFeed<T>(path: string | null) {
  const [state, setState] = useState<{ path: string | null; data: T | null; error: boolean; fetchedAt: number }>({ path: null, data: null, error: false, fetchedAt: 0 });
  useEffect(() => {
    if (!path) return;
    let active = true;
    apiGet<T>(path).then(data => { if (active) setState({ path, data, error: false, fetchedAt: Date.now() }); }).catch(() => { if (active) setState({ path, data: null, error: true, fetchedAt: Date.now() }); });
    return () => { active = false; };
  }, [path]);
  const current = state.path === path;
  return { data: current ? state.data : null, error: current && state.error, loading: path !== null && !current, fetchedAt: state.fetchedAt };
}
