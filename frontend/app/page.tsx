const API = process.env.API_BASE ?? "http://localhost:8000";

async function fetchHealth() {
  try {
    const res = await fetch(`${API}/health`, { cache: "no-store" });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

async function fetchRecent<T>(path: string): Promise<T[]> {
  try {
    const res = await fetch(`${API}${path}`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export default async function OverviewPage() {
  const [health, logs, tasks, emails] = await Promise.all([
    fetchHealth(),
    fetchRecent<{ id: number; agent_name: string; task: string; status: string; created_at: string }>("/agents/logs?limit=5"),
    fetchRecent<{ id: number; title: string; status: string }>("/tasks/?status=pending"),
    fetchRecent<{ id: number; subject: string; sender: string }>("/emails/?processed=false"),
  ]);

  return (
    <div className="space-y-8 max-w-4xl">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">Command Center</h1>
        <span
          className={`px-2 py-0.5 rounded text-xs font-mono ${health ? "text-green-400" : "text-red-400"}`}
          style={{ background: "var(--surface)" }}
        >
          {health ? "● online" : "● offline"}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Pending tasks", value: tasks.length },
          { label: "Unread emails", value: emails.length },
          { label: "Agent runs today", value: logs.length },
        ].map((s) => (
          <div key={s.label} className="rounded-lg p-4" style={{ background: "var(--surface)", border: "1px solid var(--border)" }}>
            <p className="text-sm" style={{ color: "var(--muted)" }}>{s.label}</p>
            <p className="text-3xl font-bold mt-1">{s.value}</p>
          </div>
        ))}
      </div>

      <Section title="Recent Agent Activity">
        {logs.length === 0 ? (
          <Empty />
        ) : (
          logs.map((l) => (
            <Row key={l.id}>
              <Badge>{l.agent_name}</Badge>
              <span className="text-sm flex-1 truncate">{l.task}</span>
              <StatusDot ok={l.status === "success"} />
            </Row>
          ))
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--muted)" }}>
        {title}
      </h2>
      <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
        {children}
      </div>
    </div>
  );
}

function Row({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3" style={{ borderBottom: "1px solid var(--border)", background: "var(--surface)" }}>
      {children}
    </div>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="px-2 py-0.5 rounded text-xs font-mono" style={{ background: "#1e1b4b", color: "var(--accent)" }}>
      {children}
    </span>
  );
}

function StatusDot({ ok }: { ok: boolean }) {
  return <span className={`text-xs ${ok ? "text-green-400" : "text-red-400"}`}>{ok ? "●" : "●"}</span>;
}

function Empty() {
  return (
    <div className="px-4 py-6 text-sm text-center" style={{ color: "var(--muted)", background: "var(--surface)" }}>
      Nothing here yet.
    </div>
  );
}
