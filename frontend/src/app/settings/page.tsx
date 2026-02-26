"use client";

import { useMemo, useState } from "react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type SettingsForm = {
  retentionDays: number;
  alertThreshold: number;
  autoAcknowledge: "Off" | "5 min" | "15 min";
};

const DEFAULT_SETTINGS: SettingsForm = {
  retentionDays: 14,
  alertThreshold: 0.9,
  autoAcknowledge: "Off",
};

export default function SettingsPage() {
  const [form, setForm] = useState<SettingsForm>(DEFAULT_SETTINGS);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  const isDirty = useMemo(() => JSON.stringify(form) !== JSON.stringify(DEFAULT_SETTINGS), [form]);

  function updateField<K extends keyof SettingsForm>(key: K, value: SettingsForm[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <DashboardShell>
      <section className="space-y-4">
        <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h1 className="text-xl font-semibold text-slate-800 dark:text-slate-100">System Settings</h1>
            <div className="flex items-center gap-2">
              <Badge className="border-transparent bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-100">
                Static Mode
              </Badge>
              {savedAt ? (
                <Badge className="border-transparent bg-emerald-100 text-emerald-700">
                  Saved at {savedAt}
                </Badge>
              ) : null}
            </div>
          </div>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Local configuration preview for Sprint 1. No backend persistence yet.
          </p>
        </div>

        <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Retention & Alerts
          </h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Data Retention (days)
              <Input
                type="number"
                value={form.retentionDays}
                onChange={(event) => {
                  const value = Number(event.target.value);
                  if (!Number.isNaN(value)) {
                    updateField("retentionDays", value);
                  }
                }}
                className="mt-1 border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </label>

            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Alert Threshold (0 - 1)
              <Input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={form.alertThreshold}
                onChange={(event) => {
                  const value = Number(event.target.value);
                  if (!Number.isNaN(value)) {
                    updateField("alertThreshold", value);
                  }
                }}
                className="mt-1 border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
              />
            </label>
          </div>
        </section>

        <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Workflow</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Auto-acknowledge Incidents
              <Select
                value={form.autoAcknowledge}
                onValueChange={(value) =>
                  updateField("autoAcknowledge", value as SettingsForm["autoAcknowledge"])
                }
              >
                <SelectTrigger className="mt-1 w-full border-slate-300 bg-slate-50 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Off">Off</SelectItem>
                  <SelectItem value="5 min">5 min</SelectItem>
                  <SelectItem value="15 min">15 min</SelectItem>
                </SelectContent>
              </Select>
            </label>
          </div>
        </section>

        <div className="flex items-center justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={!isDirty}
            onClick={() => {
              setForm(DEFAULT_SETTINGS);
              setSavedAt(null);
            }}
            className="border-slate-300 bg-slate-100 text-sm font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            Reset Defaults
          </Button>
          <Button
            type="button"
            disabled={!isDirty}
            onClick={() => setSavedAt(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }))}
            className="bg-cyan-500 text-white hover:bg-cyan-600"
          >
            Save Settings
          </Button>
        </div>
      </section>
    </DashboardShell>
  );
}
