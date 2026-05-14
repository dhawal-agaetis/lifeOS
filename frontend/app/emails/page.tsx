const API = process.env.API_BASE ?? "http://localhost:8000";

type EmailRow = {
  id: number;
  gmail_id: string;
  subject: string;
  sender: string;
  body_preview: string;
  processed: boolean;
  created_at: string;
};

async function fetchEmails(): Promise<EmailRow[]> {
  try {
    const res = await fetch(`${API}/emails/`, { cache: "no-store" });
    return res.ok ? await res.json() : [];
  } catch {
    return [];
  }
}

export default async function EmailsPage() {
  const emails = await fetchEmails();

  return (
    <div className="max-w-4xl space-y-4">
      <h1 className="text-2xl font-bold">Emails</h1>
      {emails.length === 0 ? (
        <p style={{ color: "var(--muted)" }} className="text-sm">No emails processed yet.</p>
      ) : (
        <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
          {emails.map((e) => (
            <div
              key={e.id}
              className="px-5 py-4 space-y-1"
              style={{ borderBottom: "1px solid var(--border)", background: "var(--surface)" }}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-sm">{e.subject || "(no subject)"}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${e.processed ? "text-green-400" : "text-yellow-400"}`}
                  style={{ background: "var(--bg)" }}>
                  {e.processed ? "processed" : "unread"}
                </span>
              </div>
              <p className="text-xs" style={{ color: "var(--muted)" }}>{e.sender}</p>
              {e.body_preview && (
                <p className="text-xs truncate" style={{ color: "var(--muted)" }}>{e.body_preview}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
