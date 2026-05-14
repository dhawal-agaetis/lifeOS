const API = process.env.API_BASE ?? "http://localhost:8000";

type TaskRow = {
  id: number;
  title: string;
  description: string;
  status: string;
  agent: string;
  due_at: string | null;
  created_at: string;
};

async function fetchTasks(): Promise<TaskRow[]> {
  try {
    const res = await fetch(`${API}/tasks/`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

const statusColor: Record<string, string> = {
  pending: "text-yellow-400",
  done: "text-green-400",
  failed: "text-red-400",
};

export default async function TasksPage() {
  const tasks = await fetchTasks();

  return (
    <div className="max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Tasks</h1>
      {tasks.length === 0 ? (
        <p style={{ color: "var(--muted)" }} className="text-sm">No tasks yet.</p>
      ) : (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
          {tasks.map((t) => (
            <div
              key={t.id}
              className="px-5 py-4 flex items-start gap-4"
              style={{ borderBottom: "1px solid var(--border)", background: "var(--surface)" }}
            >
              <span className={`text-xs pt-0.5 font-mono ${statusColor[t.status] ?? "text-gray-400"}`}>
                {t.status}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{t.title}</p>
                {t.description && (
                  <p className="text-xs mt-0.5 line-clamp-2" style={{ color: "var(--muted)" }}>{t.description}</p>
                )}
              </div>
              {t.agent && (
                <span className="text-xs px-2 py-0.5 rounded font-mono" style={{ background: "#1e1b4b", color: "var(--accent)" }}>
                  {t.agent}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
