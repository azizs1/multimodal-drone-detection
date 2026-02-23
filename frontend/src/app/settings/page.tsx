import { DashboardShell } from "@/components/layout/dashboard-shell";

export default function SettingsPage() {
  return (
    <DashboardShell>
      <section className="rounded-lg border border-slate-200 bg-slate-50 p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="mt-2 text-slate-600">
          Settings page placeholder for retention and threshold controls.
        </p>
      </section>
    </DashboardShell>
  );
}
