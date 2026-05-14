const API = process.env.API_BASE ?? "http://localhost:8000";

type LogRow = {
  id: number;
  agent_name: string;
  task: string;
  result: string;
  status: string;
  created_at: string;
};

async function fetchLogs(): Promise<LogRow[]> {
  try {
    const res = await fetch(`${API}/agents/logs`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export default async function LogsPage() {
  const logs = await fetchLogs();

  return (
    <div className="max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Agent Logs</h1>
      {logs.length === 0 ? (
        <p style={{ color: "var(--muted)" }} className="text-sm">No agent activity yet.</p>
      ) : (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
          {logs.map((l) => (
            <div
              key={l.id}
              className="px-5 py-4 space-y-1"
              style={{ borderBottom: "1px solid var(--border)", background: "var(--surface)" }}
            >
              <div className="flex items-center gap-3">
                <span className="text-xs px-2 py-0.5 rounded font-mono" style={{ background: "#eef2ff", color: "var(--accent)" }}>
                  {l.agent_name}
                </span>
                <span className={`text-xs ${l.status === "success" ? "text-green-600" : "text-red-500"}`}>
                  {l.status}
                </span>
                <span className="text-xs ml-auto" style={{ color: "var(--muted)" }}>
                  {new Date(l.created_at).toLocaleString()}
                </span>
              </div>
              <p className="text-sm">{l.task}</p>
              {l.result && (
                <p className="text-xs line-clamp-3" style={{ color: "var(--muted)" }}>{l.result}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
