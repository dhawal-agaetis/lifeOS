"use client";

import { useEffect, useState, useCallback } from "react";

const API = process.env.API_BASE ?? "http://localhost:8000";
const REFRESH_MS = 5 * 60 * 1000;

type OrderItem = {
  product_name: string;
  product_sku: string;
  quantity: number;
  unit_price: number | null;
  line_total: number | null;
};

type Customer = {
  name: string | null;
  email: string | null;
  postcode: string | null;
  phone: string | null;
};

type Order = {
  order_id: string;
  date_added: string | null;
  status: string | null;
  subtotal: number | null;
  vat: number | null;
  grand_total: number | null;
  comments: string | null;
  deliver_by: string | null;
  is_business_customer: boolean;
  customer: Customer | null;
  items: OrderItem[];
};

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

type AllData = {
  total: number;
  orders: Order[];
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
  const [allData, setAllData] = useState<AllData | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortBy, setSortBy] = useState<"date" | "total">("date");
  const [sortDir, setSortDir] = useState<"desc" | "asc">("desc");

  const load = useCallback(async () => {
    const params = new URLSearchParams({ limit: "200" });
    if (statusFilter) params.set("status", statusFilter);
    if (dateFrom) params.set("date_from", toApiDate(dateFrom));
    if (dateTo) params.set("date_to", toApiDate(dateTo));

    const [t, s, a] = await Promise.all([
      get<TodayData>("/orders/today"),
      get<SummaryData>("/orders/summary"),
      get<AllData>(`/orders/all?${params}`),
    ]);
    setToday(t);
    setSummary(s);
    setAllData(a);
  }, [statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => clearInterval(interval);
  }, [load]);

  const orders = allData?.orders ?? [];
  const sorted = [...orders].sort((a, b) => {
    let av: number, bv: number;
    if (sortBy === "total") {
      av = a.grand_total ?? 0;
      bv = b.grand_total ?? 0;
    } else {
      av = parseDdMmYyyy(a.date_added);
      bv = parseDdMmYyyy(b.date_added);
    }
    return sortDir === "desc" ? bv - av : av - bv;
  });

  function toggleSort(col: "date" | "total") {
    if (sortBy === col) setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    else { setSortBy(col); setSortDir("desc"); }
  }

  return (
    <div className="max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold">House of Worktops</h1>

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
            value={summary.highest_revenue_in_a_day.amount ? `£${summary.highest_revenue_in_a_day.amount.toFixed(2)}` : "—"}
            sub={summary.highest_revenue_in_a_day.date ?? ""}
          />
          <RecordCard
            label="Average order value"
            value={`£${summary.average_order_value.toFixed(2)}`}
            sub={`across ${summary.total_orders} orders`}
          />
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 items-end flex-wrap">
        <FilterField label="Status">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-transparent border rounded px-2 py-1 text-sm"
            style={{ borderColor: "var(--border)", color: "var(--text)" }}
          >
            <option value="">All statuses</option>
            {Object.keys(summary?.orders_by_status ?? {}).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </FilterField>
        <FilterField label="From (DD/MM/YYYY)">
          <input
            type="text"
            placeholder="01/01/2026"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="bg-transparent border rounded px-2 py-1 text-sm w-32"
            style={{ borderColor: "var(--border)", color: "var(--text)" }}
          />
        </FilterField>
        <FilterField label="To (DD/MM/YYYY)">
          <input
            type="text"
            placeholder="31/12/2026"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="bg-transparent border rounded px-2 py-1 text-sm w-32"
            style={{ borderColor: "var(--border)", color: "var(--text)" }}
          />
        </FilterField>
        <button
          onClick={load}
          className="px-3 py-1 rounded text-sm"
          style={{ background: "var(--accent)", color: "#fff" }}
        >
          Filter
        </button>
      </div>

      {/* Orders table */}
      <div>
        <div
          className="rounded-t-lg grid text-xs font-semibold uppercase tracking-wider px-4 py-2"
          style={{
            background: "var(--bg)",
            color: "var(--muted)",
            gridTemplateColumns: "7rem 7rem 1fr 3rem 6rem 6rem 6rem",
            border: "1px solid var(--border)",
            borderBottom: "none",
          }}
        >
          <SortHeader col="date" current={sortBy} dir={sortDir} onToggle={toggleSort}>Date</SortHeader>
          <span>Order ID</span>
          <span>Customer</span>
          <span className="text-right">Items</span>
          <span>Postcode</span>
          <SortHeader col="total" current={sortBy} dir={sortDir} onToggle={toggleSort}>Total</SortHeader>
          <span>Status</span>
        </div>
        <div className="rounded-b-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
          {sorted.length === 0 ? (
            <div className="px-4 py-8 text-sm text-center" style={{ color: "var(--muted)", background: "var(--surface)" }}>
              No orders found.
            </div>
          ) : (
            sorted.map((o) => (
              <OrderRow
                key={o.order_id}
                order={o}
                expanded={expandedId === o.order_id}
                onToggle={() => setExpandedId(expandedId === o.order_id ? null : o.order_id)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function OrderRow({ order: o, expanded, onToggle }: { order: Order; expanded: boolean; onToggle: () => void }) {
  return (
    <>
      <div
        onClick={onToggle}
        className="grid px-4 py-3 cursor-pointer text-sm transition-colors"
        style={{
          borderBottom: "1px solid var(--border)",
          background: expanded ? "#1e1b4b22" : "var(--surface)",
          gridTemplateColumns: "7rem 7rem 1fr 3rem 6rem 6rem 6rem",
        }}
      >
        <span style={{ color: "var(--muted)" }}>{o.date_added ?? "—"}</span>
        <span className="font-mono" style={{ color: "var(--accent)" }}>{o.order_id}</span>
        <span className="truncate">{o.customer?.name ?? "—"}</span>
        <span className="text-right">{o.items.length}</span>
        <span style={{ color: "var(--muted)" }}>{o.customer?.postcode ?? "—"}</span>
        <span className="font-medium">{o.grand_total != null ? `£${o.grand_total.toFixed(2)}` : "—"}</span>
        <StatusBadge status={o.status} />
      </div>
      {expanded && <OrderDetail order={o} />}
    </>
  );
}

function OrderDetail({ order: o }: { order: Order }) {
  return (
    <div
      className="px-6 py-4 text-sm space-y-4"
      style={{ background: "#111", borderBottom: "1px solid var(--border)" }}
    >
      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--muted)" }}>Customer</p>
          <p>{o.customer?.name ?? "—"}</p>
          <p style={{ color: "var(--muted)" }}>{o.customer?.email ?? "—"}</p>
          <p style={{ color: "var(--muted)" }}>{o.customer?.phone ?? "—"}</p>
          <p style={{ color: "var(--muted)" }}>{o.customer?.postcode ?? "—"}</p>
          {o.is_business_customer && (
            <span className="text-xs px-2 py-0.5 rounded" style={{ background: "#1e1b4b", color: "var(--accent)" }}>
              Business customer
            </span>
          )}
        </div>
        <div className="space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--muted)" }}>Order details</p>
          <p>Status: <span className="font-medium">{o.status ?? "—"}</span></p>
          {o.deliver_by && <p>Deliver by: {o.deliver_by}</p>}
          {o.comments && <p style={{ color: "var(--muted)" }}>"{o.comments}"</p>}
        </div>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--muted)" }}>Products</p>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left" style={{ color: "var(--muted)" }}>
              <th className="pb-1 font-normal">Product</th>
              <th className="pb-1 font-normal text-right w-12">Qty</th>
              <th className="pb-1 font-normal text-right w-24">Unit</th>
              <th className="pb-1 font-normal text-right w-24">Total</th>
            </tr>
          </thead>
          <tbody>
            {o.items.map((item, i) => (
              <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
                <td className="py-1.5">
                  <span>{item.product_name}</span>
                  <span className="ml-2 text-xs font-mono" style={{ color: "var(--muted)" }}>({item.product_sku})</span>
                </td>
                <td className="py-1.5 text-right">{item.quantity}</td>
                <td className="py-1.5 text-right">{item.unit_price != null ? `£${item.unit_price.toFixed(2)}` : "—"}</td>
                <td className="py-1.5 text-right font-medium">{item.line_total != null ? `£${item.line_total.toFixed(2)}` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex gap-8 text-sm pt-1" style={{ borderTop: "1px solid var(--border)" }}>
        <span style={{ color: "var(--muted)" }}>Subtotal: {o.subtotal != null ? `£${o.subtotal.toFixed(2)}` : "—"}</span>
        <span style={{ color: "var(--muted)" }}>VAT: {o.vat != null ? `£${o.vat.toFixed(2)}` : "—"}</span>
        <span className="font-bold">Total: {o.grand_total != null ? `£${o.grand_total.toFixed(2)}` : "—"}</span>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg p-4" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
      <p className="text-sm" style={{ color: "var(--muted)" }}>{label}</p>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
  );
}

function RecordCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-lg p-4" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
      <p className="text-xs uppercase tracking-wider" style={{ color: "var(--muted)" }}>{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: "var(--muted)" }}>{sub}</p>}
    </div>
  );
}

function FilterField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs" style={{ color: "var(--muted)" }}>{label}</label>
      {children}
    </div>
  );
}

function SortHeader({
  col, current, dir, onToggle, children,
}: {
  col: "date" | "total";
  current: string;
  dir: string;
  onToggle: (col: "date" | "total") => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={() => onToggle(col)}
      className="flex items-center gap-1 text-left"
      style={{ color: current === col ? "var(--accent)" : "var(--muted)" }}
    >
      {children}
      {current === col && <span>{dir === "desc" ? "↓" : "↑"}</span>}
    </button>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  const colour = status?.toLowerCase() === "processing"
    ? "text-yellow-400"
    : status?.toLowerCase() === "complete" || status?.toLowerCase() === "completed"
    ? "text-green-400"
    : "text-gray-400";
  return <span className={`text-xs ${colour}`}>{status ?? "—"}</span>;
}

function parseDdMmYyyy(s: string | null): number {
  if (!s) return 0;
  const parts = s.split("/");
  if (parts.length !== 3) return 0;
  return new Date(`${parts[2]}-${parts[1]}-${parts[0]}`).getTime();
}

function toApiDate(ddmmyyyy: string): string {
  // API expects DD/MM/YYYY — pass straight through
  return ddmmyyyy;
}
