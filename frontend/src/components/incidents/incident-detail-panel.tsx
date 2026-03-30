"use client";

import { format } from "date-fns";
import {
  INCIDENT_STATUS_BADGE_CLASSES,
  type IncidentDetailPanelData,
} from "@/lib/incidents.mjs";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type IncidentDetailPanelProps = {
  incident: IncidentDetailPanelData | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

function formatIncidentTimestamp(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return format(date, "yyyy-MM-dd HH:mm:ss");
}

function DetailBlock({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </p>
      <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  );
}

export function IncidentDetailPanel({
  incident,
  open,
  onOpenChange,
}: IncidentDetailPanelProps) {
  return (
      <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="top-0 right-0 left-auto h-screen max-w-[720px] translate-x-0 translate-y-0 rounded-none border-y-0 border-r-0 border-l border-slate-200 bg-slate-50 p-0 duration-300 data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-[720px] dark:border-slate-800 dark:bg-slate-950">
        <div className="flex h-full flex-col overflow-hidden">
          <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-800">
            <DialogHeader className="space-y-3 text-left">
              <div className="flex flex-wrap items-center gap-3">
                <DialogTitle className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
                  Incident {incident?.id ?? "--"}
                </DialogTitle>
                {incident ? (
                  <Badge className={`px-3 py-1 text-sm font-semibold ${INCIDENT_STATUS_BADGE_CLASSES[incident.status]}`}>
                    {incident.status}
                  </Badge>
                ) : null}
              </div>
              <DialogDescription className="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                Review the fused detection summary, modality evidence, and media references for
                the selected incident.
              </DialogDescription>
            </DialogHeader>
          </div>

          <div className="flex-1 overflow-y-auto px-6 py-6">
            <div className="space-y-6">
              <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Decision Summary
                    </p>
                    <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
                      {incident ? `${incident.fusedConfidence}%` : "--"}
                    </p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                      Fused confidence
                    </p>
                  </div>

                  <div className="min-w-44 space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
                    <DetailBlock label="Decision" value={incident?.decision ?? "--"} />
                    <DetailBlock label="Band" value={incident?.confidenceBand ?? "--"} />
                    <DetailBlock
                      label="Latency"
                      value={incident ? `${incident.latencyMs} ms` : "--"}
                    />
                  </div>
                </div>

                <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Gating Reason
                  </p>
                  <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
                    {incident?.gatingReason ?? "Fusion gating and threshold reasoning will appear here."}
                  </p>
                </div>
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Per-Modality Scores
                </p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      RGB
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                      {incident ? `${incident.visualScore}%` : "--"}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Thermal
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                      {incident ? `${incident.thermalScore}%` : "--"}
                    </p>
                  </div>
                </div>
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Media References
                </p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-dashed border-slate-300 bg-slate-100/80 p-4 dark:border-slate-700 dark:bg-slate-950">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      RGB Media
                    </p>
                    <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
                      {incident?.rgbMediaLabel ?? "RGB media reference will appear here."}
                    </p>
                  </div>
                  <div className="rounded-lg border border-dashed border-slate-300 bg-slate-100/80 p-4 dark:border-slate-700 dark:bg-slate-950">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Thermal Media
                    </p>
                    <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
                      {incident?.thermalMediaLabel ?? "Thermal media reference will appear here."}
                    </p>
                  </div>
                </div>
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Thresholds
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {incident?.thresholdLabel ?? "Configured threshold values will be summarized here."}
                  </p>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Objects / Overlay
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                    {incident?.objectsLabel ?? "Detected objects and overlay-ready summaries will appear here."}
                  </p>
                </div>
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Event Metadata
                </p>
                <div className="mt-4 grid gap-5 sm:grid-cols-2">
                  <DetailBlock
                    label="Timestamp"
                    value={incident ? formatIncidentTimestamp(incident.timestamp) : "--"}
                  />
                  <DetailBlock label="Status" value={incident?.status ?? "--"} />
                </div>
              </section>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
