import { DashboardShell } from "@/components/layout/dashboard-shell";

export default function LiveFeedPage() {
  return (
    <DashboardShell>
      <section className="rounded-lg border border-slate-200 bg-slate-50 p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Live Feed</h1>
        <p className="mt-2 text-slate-600">
          Live feed content (Sprint 1 static UI in next commit).
        </p>
      </section>
    </DashboardShell>
  );
}
