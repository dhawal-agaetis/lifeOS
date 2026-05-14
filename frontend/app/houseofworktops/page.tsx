"use client";

import { useEffect, useState, useCallback } from "react";

const API = "http://localhost:8000";
const REFRESH_MS = 60 * 1000;

type TodayData = {
  count: number;
  total_revenue: number;
  orders: { order_id: string; date_added: string; status: string; grand_total: number | null }[];
};

type SummaryData = {
  total_orders: number;
  total_revenue: number;
  average_order_value: number;
  highest_orders_in_a_day: { date: string | null; count: number };
  highest_revenue_in_a_day: { date: string | null; amount: number };
  orders_by_status: Record<string, number>;
  top_products: { product: string; total_quantity: number }[];
};

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API}${path}`, { cache: "no-store" });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

export default function HouseOfWorktopsPage() {
  const [today, setToday] = useState<TodayData | null>(null);
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [now, setNow] = useState(() => new Date());

  const load = useCallback(async () => {
    const [t, s] = await Promise.all([
      get<TodayData>("/orders/today"),
      get<SummaryData>("/orders/summary"),
    ]);
    setToday(t);
    setSummary(s);
    setLastUpdated(new Date());
  }, []);

  useEffect(() => {
    load();
    const refresh = setInterval(load, REFRESH_MS);
    return () => clearInterval(refresh);
  }, [load]);

  // Tick every second so "last updated" counter stays live
  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(tick);
  }, []);

  const secondsAgo = lastUpdated ? Math.floor((now.getTime() - lastUpdated.getTime()) / 1000) : null;

  return (
    <div className="min-h-screen" style={{ background: "#f8fafc" }}>
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold" style={{ color: "#0f172a" }}>
            House of Worktops
          </h1>
          <span className="text-xs" style={{ color: "#94a3b8" }}>
            {secondsAgo === null
              ? "Loading…"
              : secondsAgo < 5
              ? "Just updated"
              : `Last updated: ${secondsAgo}s ago`}
          </span>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Orders today", value: today?.count ?? "—" },
            { label: "Revenue today", value: today ? `£${today.total_revenue.toFixed(2)}` : "—" },
            { label: "All time orders", value: summary?.total_orders ?? "—" },
            { label: "All time revenue", value: summary ? `£${summary.total_revenue.toFixed(2)}` : "—" },
          ].map((s) => (
            <StatCard key={s.label} label={s.label} value={String(s.value)} />
          ))}
        </div>

        {/* Record cards */}
        {summary && (
          <div className="grid grid-cols-3 gap-4">
            <RecordCard
              label="Highest orders in a day"
              value={String(summary.highest_orders_in_a_day.count || "—")}
              sub={summary.highest_orders_in_a_day.date ?? ""}
            />
            <RecordCard
              label="Highest revenue in a day"
              value={
                summary.highest_revenue_in_a_day.amount
                  ? `£${summary.highest_revenue_in_a_day.amount.toFixed(2)}`
                  : "—"
              }
              sub={summary.highest_revenue_in_a_day.date ?? ""}
            />
            <RecordCard
              label="Average order value"
              value={`£${summary.average_order_value.toFixed(2)}`}
              sub={`across ${summary.total_orders} orders`}
            />
          </div>
        )}

        {/* Status breakdown */}
        {summary && Object.keys(summary.orders_by_status).length > 0 && (
          <Section title="Orders by status">
            <div className="flex flex-wrap gap-3">
              {Object.entries(summary.orders_by_status).map(([status, count]) => (
                <div
                  key={status}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm"
                  style={{ background: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}
                >
                  <span style={{ color: statusColour(status) }}>●</span>
                  <span style={{ color: "#374151" }}>{status}</span>
                  <span className="font-semibold" style={{ color: "#0f172a" }}>{count}</span>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Top products */}
        {summary && summary.top_products.length > 0 && (
          <Section title="Top products">
            <div className="space-y-2">
              {summary.top_products.map((p, i) => (
                <div
                  key={p.product}
                  className="flex items-center justify-between px-4 py-2.5 rounded-lg text-sm"
                  style={{ background: "#fff", border: "1px solid #e2e8f0", boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono w-5 text-right" style={{ color: "#94a3b8" }}>{i + 1}</span>
                    <span style={{ color: "#374151" }}>{p.product}</span>
                  </div>
                  <span className="font-semibold" style={{ color: "#0f172a" }}>×{p.total_quantity}</span>
                </div>
              ))}
            </div>
          </Section>
        )}

      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="rounded-xl p-5"
      style={{
        background: "#fff",
        border: "1px solid #e2e8f0",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <p className="text-xs uppercase tracking-wider font-medium" style={{ color: "#94a3b8" }}>{label}</p>
      <p className="text-3xl font-bold mt-2" style={{ color: "#0f172a" }}>{value}</p>
    </div>
  );
}

function RecordCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div
      className="rounded-xl p-5"
      style={{
        background: "#fff",
        border: "1px solid #e2e8f0",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <p className="text-xs uppercase tracking-wider font-medium" style={{ color: "#94a3b8" }}>{label}</p>
      <p className="text-2xl font-bold mt-2" style={{ color: "#0f172a" }}>{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: "#94a3b8" }}>{sub}</p>}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wider" style={{ color: "#64748b" }}>{title}</h2>
      {children}
    </div>
  );
}

function statusColour(status: string): string {
  const s = status.toLowerCase();
  if (s === "processing") return "#f59e0b";
  if (s === "complete" || s === "completed") return "#10b981";
  if (s === "cancelled" || s === "canceled") return "#ef4444";
  return "#94a3b8";
}
