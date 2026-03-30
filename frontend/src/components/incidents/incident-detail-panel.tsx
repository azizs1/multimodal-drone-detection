"use client";

import { format } from "date-fns";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export type IncidentPanelStatus = "Confirmed" | "Pending" | "False Positive";

export type IncidentDetailPanelData = {
  id: string;
  timestamp: string;
  confidence: number;
  distanceFt: number;
  model: string;
  status: IncidentPanelStatus;
  source: "Fusion" | "Visual" | "Thermal";
  summary: string;
  imageLabel?: string;
};

type IncidentDetailPanelProps = {
  incident: IncidentDetailPanelData | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const STATUS_BADGE_CLASSES: Record<IncidentPanelStatus, string> = {
  Confirmed:
    "border-transparent bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  Pending:
    "border-transparent bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  "False Positive":
    "border-transparent bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
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
      <DialogContent className="max-w-3xl border-slate-200 bg-slate-50 p-0 dark:border-slate-800 dark:bg-slate-900">
        <div className="grid gap-0 md:grid-cols-[1.15fr_0.85fr]">
          <div className="border-b border-slate-200 p-6 dark:border-slate-800 md:border-r md:border-b-0">
            <DialogHeader className="space-y-3 text-left">
              <div className="flex flex-wrap items-center gap-3">
                <DialogTitle className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
                  Incident {incident?.id ?? "--"}
                </DialogTitle>
                {incident ? (
                  <Badge className={`px-3 py-1 text-sm font-semibold ${STATUS_BADGE_CLASSES[incident.status]}`}>
                    {incident.status}
                  </Badge>
                ) : null}
              </div>
              <DialogDescription className="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
                {incident?.summary ??
                  "Select an incident from the table to review its detection summary and supporting details."}
              </DialogDescription>
            </DialogHeader>

            <div className="mt-6 rounded-lg border border-dashed border-slate-300 bg-slate-100/80 p-6 dark:border-slate-700 dark:bg-slate-800/60">
              <div className="flex min-h-56 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-center dark:border-slate-700 dark:bg-slate-900">
                <div className="space-y-2 px-6">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Media Preview
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    {incident?.imageLabel ?? "Snapshot or evidence preview will appear here."}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6 p-6">
            <div className="grid gap-5 sm:grid-cols-2 md:grid-cols-1 xl:grid-cols-2">
              <DetailBlock
                label="Timestamp"
                value={incident ? formatIncidentTimestamp(incident.timestamp) : "--"}
              />
              <DetailBlock
                label="Confidence"
                value={incident ? `${incident.confidence}%` : "--"}
              />
              <DetailBlock
                label="Distance"
                value={incident ? `${incident.distanceFt}ft` : "--"}
              />
              <DetailBlock label="Source" value={incident?.source ?? "--"} />
              <DetailBlock label="Model" value={incident?.model ?? "--"} />
              <DetailBlock label="Status" value={incident?.status ?? "--"} />
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-100/70 p-4 dark:border-slate-800 dark:bg-slate-800/70">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Analyst Notes
              </p>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">
                Additional evidence, operator annotations, and resolution notes can be surfaced in
                this section when the incident data contract is ready.
              </p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
