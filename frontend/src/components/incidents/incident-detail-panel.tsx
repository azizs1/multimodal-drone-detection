"use client";

import { Check, Copy } from "lucide-react";
import { format } from "date-fns";
import { useEffect, useState } from "react";
import { type IncidentDetailPanelData } from "@/lib/incidents.mjs";
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

type MediaReferenceCardProps = {
  label: string;
  media: IncidentDetailPanelData["rgbMedia"];
};

const percentFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 1,
});

const latencyFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

function formatIncidentTimestamp(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return format(date, "yyyy-MM-dd HH:mm:ss");
}

function formatPercent(value: number): string {
  const normalized = value <= 1 ? value * 100 : value;
  return `${percentFormatter.format(normalized)}%`;
}

function formatLatency(value: number): string {
  return `${latencyFormatter.format(value)} ms`;
}

function formatCount(value: number | null): string {
  return typeof value === "number" ? String(value) : "--";
}

function formatDuration(start: string | null, end: string | null): string {
  if (!start || !end) {
    return "--";
  }

  const startTime = new Date(start).getTime();
  const endTime = new Date(end).getTime();

  if (Number.isNaN(startTime) || Number.isNaN(endTime)) {
    return "--";
  }

  const seconds = Math.max(0, (endTime - startTime) / 1000);
  return `${latencyFormatter.format(seconds)} s`;
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

function MetadataGrid({
  items,
}: {
  items: Array<{ label: string; value: string }>;
}) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      {items.map((item) => (
        <DetailBlock key={item.label} label={item.label} value={item.value} />
      ))}
    </div>
  );
}

function MediaLink({ href, children }: { href: string; children: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex w-fit items-center rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
    >
      {children}
    </a>
  );
}

function MediaReferenceCard({ label, media }: MediaReferenceCardProps) {
  const hasFrame = Boolean(media.frameUrl);
  const hasThumbnail = Boolean(media.thumbnailUrl);

  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-100/80 p-4 dark:border-slate-700 dark:bg-slate-950">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </p>
      {hasFrame || hasThumbnail ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {media.frameUrl ? <MediaLink href={media.frameUrl}>Frame link</MediaLink> : null}
          {media.thumbnailUrl ? (
            <MediaLink href={media.thumbnailUrl}>Thumbnail link</MediaLink>
          ) : null}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">No media available</p>
      )}
    </div>
  );
}

export function IncidentDetailPanel({
  incident,
  open,
  onOpenChange,
}: IncidentDetailPanelProps) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) {
      return undefined;
    }

    const timeout = window.setTimeout(() => {
      setCopied(false);
    }, 1500);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [copied]);

  const handleCopyIncidentId = async () => {
    if (!incident?.id) {
      return;
    }

    try {
      await navigator.clipboard.writeText(incident.id);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  const metadataItems = incident
    ? [
        { label: "Detected At", value: formatIncidentTimestamp(incident.timestamp) },
        { label: "Decision", value: incident.decision },
        { label: "Alert Level", value: incident.alertLevel },
        { label: "Confidence Band", value: incident.confidenceBand },
      ]
    : [
        { label: "Detected At", value: "--" },
        { label: "Decision", value: "--" },
        { label: "Alert Level", value: "--" },
        { label: "Confidence Band", value: "--" },
      ];
  const aggregateItems =
    incident && incident.isAggregated
      ? [
          { label: "Event Start", value: formatIncidentTimestamp(incident.startedAt ?? incident.timestamp) },
          {
            label: "Last Seen",
            value: formatIncidentTimestamp(incident.lastSeenAt ?? incident.timestamp),
          },
          {
            label: "Event End",
            value: incident.endedAt ? formatIncidentTimestamp(incident.endedAt) : "--",
          },
          { label: "Total Frames", value: formatCount(incident.frameCount) },
          { label: "Drone Frames", value: formatCount(incident.droneFrameCount) },
          {
            label: "Duration",
            value: formatDuration(incident.startedAt, incident.lastSeenAt),
          },
          {
            label: "Avg Confidence",
            value:
              typeof incident.avgFusedConfidence === "number"
                ? formatPercent(incident.avgFusedConfidence)
                : "--",
          },
          { label: "Representative Raw ID", value: incident.representativeIncidentId ?? "--" },
          {
            label: "Raw IDs",
            value:
              incident.rawIncidentIds.length > 0
                ? incident.rawIncidentIds.slice(0, 4).join(", ")
                : "--",
          },
        ]
      : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="top-0 right-0 left-auto h-screen max-w-[720px] translate-x-0 translate-y-0 rounded-none border-y-0 border-r-0 border-l border-slate-200 bg-slate-50 p-0 duration-300 data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-[720px] dark:border-slate-800 dark:bg-slate-950">
        <div className="flex h-full flex-col overflow-hidden">
          <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-800">
            <DialogHeader className="space-y-2 text-left">
              <div className="max-w-full space-y-2 pr-8">
                <DialogTitle className="text-base font-medium tracking-normal text-slate-500 dark:text-slate-400">
                  <button
                    type="button"
                    onClick={() => void handleCopyIncidentId()}
                    disabled={!incident?.id}
                    className="inline-flex max-w-full items-center gap-2 rounded-md border border-slate-200 bg-slate-100 px-3 py-2 font-mono text-sm text-slate-600 transition-colors hover:bg-slate-200 disabled:cursor-default disabled:hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    <span className="truncate">{incident?.id ?? "--"}</span>
                    {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                  </button>
                </DialogTitle>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Click to copy incident ID
                </p>
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
                      {incident?.isAggregated ? "Aggregated Decision Summary" : "Decision Summary"}
                    </p>
                    <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
                      {incident ? formatPercent(incident.fusedConfidence) : "--"}
                    </p>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                      {incident?.isAggregated ? "Max fused confidence" : "Fused confidence"}
                    </p>
                  </div>

                  <div className="min-w-44 space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950">
                    {incident?.isAggregated ? (
                      <>
                        <DetailBlock label="Frames" value={formatCount(incident.frameCount)} />
                        <DetailBlock
                          label="Avg Confidence"
                          value={
                            typeof incident.avgFusedConfidence === "number"
                              ? formatPercent(incident.avgFusedConfidence)
                              : "--"
                          }
                        />
                        <DetailBlock
                          label="Duration"
                          value={formatDuration(incident.startedAt, incident.lastSeenAt)}
                        />
                      </>
                    ) : (
                      <>
                        <DetailBlock label="Decision" value={incident?.decision ?? "--"} />
                        <DetailBlock label="Band" value={incident?.confidenceBand ?? "--"} />
                        <DetailBlock
                          label="Latency"
                          value={incident ? formatLatency(incident.latencyMs) : "--"}
                        />
                      </>
                    )}
                  </div>
                </div>

                <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Gating Reason
                  </p>
                  <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
                    {incident?.gatingReason ?? "--"}
                  </p>
                </div>
              </section>

              {incident?.isAggregated ? (
                <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Aggregate Event
                  </p>
                  <div className="mt-4">
                    <MetadataGrid items={aggregateItems} />
                  </div>
                </section>
              ) : null}

              <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {incident?.isAggregated
                    ? "Average Per-Modality Scores"
                    : "Per-Modality Scores"}
                </p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      RGB
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                      {incident ? formatPercent(incident.visualScore) : "--"}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      Thermal
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-50">
                      {incident ? formatPercent(incident.thermalScore) : "--"}
                    </p>
                  </div>
                </div>
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Media References
                </p>
                <div className="mt-4 grid gap-4 sm:grid-cols-2">
                  <MediaReferenceCard
                    label="RGB Media"
                    media={incident?.rgbMedia ?? { frameUrl: null, thumbnailUrl: null }}
                  />
                  <MediaReferenceCard
                    label="Thermal Media"
                    media={incident?.thermalMedia ?? { frameUrl: null, thumbnailUrl: null }}
                  />
                </div>
              </section>

              <section className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Thresholds
                  </p>
                  {incident && incident.thresholds.length > 0 ? (
                    <div className="mt-3 space-y-3">
                      {incident.thresholds.map((threshold) => (
                        <div
                          key={threshold.key}
                          className="flex items-center justify-between gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950"
                        >
                          <span className="text-sm text-slate-600 dark:text-slate-300">
                            {threshold.label}
                          </span>
                          <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                            {formatPercent(threshold.value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      No thresholds available
                    </p>
                  )}
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Objects / Overlay
                  </p>
                  {incident && incident.objects.length > 0 ? (
                    <div className="mt-3 space-y-3">
                      {incident.objects.map((object) => (
                        <div
                          key={object.uniqueKey}
                          className="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                                {object.classId}
                              </p>
                              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                {object.modality}
                              </p>
                            </div>
                            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                              {formatPercent(object.confidence)}
                            </span>
                          </div>
                          <div className="mt-3 grid gap-3 sm:grid-cols-2">
                            <DetailBlock label="Object ID" value={object.id} />
                            <DetailBlock label="BBox" value={object.bboxLabel ?? "--"} />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                      No objects available
                    </p>
                  )}
                </div>
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Event Metadata
                </p>
                <div className="mt-4">
                  <MetadataGrid items={metadataItems} />
                </div>
              </section>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
