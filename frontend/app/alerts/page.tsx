"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/Badge";

interface AlertRule {
  id: number;
  name: string;
  module: string;
  keyword: string | null;
  enabled: boolean;
}

export default function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [name, setName] = useState("");
  const [keyword, setKeyword] = useState("");
  const [module, setModule] = useState("jobs");

  const load = () => apiGet<AlertRule[]>("/alerts/rules").then(setRules).catch(() => setRules([]));
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name) return;
    await apiPost("/alerts/rules", { name, module, keyword, delivery_channel: "telegram" });
    setName("");
    setKeyword("");
    load();
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Alerts" subtitle="Alert rules — Telegram delivery" />

      <div className="valorant-card space-y-3 p-5">
        <p className="font-valorant text-xs tracking-widest text-[var(--valorant-red)]">NEW ALERT</p>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Rule name" className="valorant-input" />
        <input value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder="Keyword (python internship)" className="valorant-input" />
        <select value={module} onChange={(e) => setModule(e.target.value)} className="valorant-input">
          <option value="jobs">Jobs</option>
          <option value="news">News</option>
          <option value="hackathons">Hackathons</option>
          <option value="all">All</option>
        </select>
        <button onClick={create} className="valorant-btn-primary">Create alert</button>
      </div>

      <div className="grid gap-3">
        {rules.map((r) => (
          <div key={r.id} className="valorant-card p-4">
            <div className="flex items-center gap-3">
              <span className="font-valorant text-lg text-white">{r.name}</span>
              <Badge>{r.module}</Badge>
            </div>
            <p className="mt-1 text-xs text-[var(--valorant-muted)]">Keyword: {r.keyword ?? "any"}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
