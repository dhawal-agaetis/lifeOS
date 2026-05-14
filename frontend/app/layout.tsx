import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "LifeOS",
  description: "Personal operating system dashboard",
};

const nav = [
  { href: "/", label: "Overview" },
  { href: "/emails", label: "Emails" },
  { href: "/tasks", label: "Tasks" },
  { href: "/logs", label: "Logs" },
  { href: "/houseofworktops", label: "House of Worktops" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen" style={{ background: "var(--bg)" }}>
        <nav
          className="flex items-center gap-6 px-8 py-4 border-b text-sm font-medium"
          style={{ borderColor: "var(--border)", background: "var(--surface)" }}
        >
          <span className="text-base font-bold tracking-tight" style={{ color: "var(--accent)" }}>
            LifeOS
          </span>
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="transition-colors hover:text-white"
              style={{ color: "var(--muted)" }}
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <main className="px-8 py-6">{children}</main>
      </body>
    </html>
  );
}
