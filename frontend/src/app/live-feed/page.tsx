"use client";

import { X } from "lucide-react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { HlsVideoPlayer } from "@/components/live-feed/hls-video-player";
import {
  buildStreamPlaylistUrl,
  buildVideoSubLabel,
} from "@/components/live-feed/live-feed-state.mjs";
import { useRealtimeAlerts } from "@/components/live-feed/use-realtime-alerts";
import { useDashboardDetectionState } from "@/components/live-feed/use-dashboard-detection-state";
import { useLiveStreams } from "@/components/live-feed/use-live-streams";
import { VideoPanel } from "@/components/live-feed/video-panel";
import { AlertBanner } from "@/components/ui/alert-banner";
import { mapRealtimeAlertToBannerData } from "@/lib/alerts";
import { type StreamInfo } from "@/lib/api/streams";
import {
  type DashboardDetectionSummary,
  type DashboardIncidentRow,
  type DashboardSystemStatus,
  type DashboardSystemStatusItem,
} from "@/lib/dashboard-detection.mjs";

function ConfidencePanel({
  summary,
}: {
  summary: DashboardDetectionSummary;
}) {
  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Primary Metrics</p>
        <div className="mt-2 grid gap-3">
          <div className="rounded-md border border-cyan-100 bg-cyan-50/60 px-3 py-4 text-center dark:border-cyan-700/50 dark:bg-slate-800">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Fused Confidence</p>
            <p className="mt-1 text-4xl font-extrabold text-cyan-500 dark:text-cyan-400">
              {summary.fusedConfidence}%
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Per-Modality Confidence
        </p>
        <div className="mt-2 grid h-28 rounded-md border border-slate-200 bg-slate-100 px-3 dark:border-slate-700 dark:bg-slate-800">
          <div className="grid grid-cols-[1fr_auto] items-center border-b border-slate-200/80 dark:border-slate-700">
            <p className="text-sm font-medium leading-none text-slate-500 dark:text-slate-400">RGB</p>
            <p className="text-2xl font-bold leading-none text-slate-500 dark:text-slate-300">
              {summary.visualConfidence}%
            </p>
          </div>
          <div className="grid grid-cols-[1fr_auto] items-center">
            <p className="text-sm font-medium leading-none text-slate-500 dark:text-slate-400">Thermal</p>
            <p className="text-2xl font-bold leading-none text-slate-500 dark:text-slate-300">
              {summary.thermalConfidence}%
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

function StreamsMetaErrorBanner({
  errorMessage,
  onRetry,
}: {
  errorMessage: string;
  onRetry: () => void;
}) {
  return (
    <div className="rounded-sm border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-800 dark:border-rose-700/60 dark:bg-rose-900/20 dark:text-rose-200">
      <div className="flex items-center justify-between gap-3">
        <p className="truncate">Failed to refresh stream metadata: {errorMessage}</p>
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 rounded border border-rose-400 px-2 py-1 text-xs font-semibold transition-colors hover:bg-rose-100 dark:border-rose-600 dark:hover:bg-rose-900/40"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

function StreamVideo({ stream, title }: { stream?: StreamInfo; title: string }) {
  if (stream?.webrtc_url) {
    return (
      <iframe
        title={title}
        src={stream.webrtc_url}
        className="h-full w-full border-0"
        allow="autoplay; fullscreen; picture-in-picture"
        allowFullScreen
      />
    );
  }

  return (
    <HlsVideoPlayer
      title={title}
      src={stream ? buildStreamPlaylistUrl(stream.name) : undefined}
    />
  );
}

function RecentIncidentsTable({
  incidents,
}: {
  incidents: DashboardIncidentRow[];
}) {
  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        Recent Incidents
      </h2>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm text-slate-600 dark:text-slate-300">
          <thead className="text-slate-500 dark:text-slate-400">
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="px-3 py-3 font-semibold">Incident ID</th>
              <th className="px-3 py-3 font-semibold">Event Start</th>
              <th className="px-3 py-3 font-semibold">Frames</th>
              <th className="px-3 py-3 font-semibold">Max Confidence</th>
              <th className="px-3 py-3 font-semibold">Avg Confidence</th>
              <th className="px-3 py-3 font-semibold">RGB Avg</th>
              <th className="px-3 py-3 font-semibold">Thermal Avg</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((row) => (
              <tr key={row.id + row.occurredAt} className="border-b border-slate-200/80 dark:border-slate-800">
                <td className="px-3 py-3">{row.id}</td>
                <td className="px-3 py-3">{row.occurredAt}</td>
                <td className="px-3 py-3">{row.frameCount ?? "--"}</td>
                <td className="px-3 py-3">{row.fusedConfidence}%</td>
                <td className="px-3 py-3">
                  {row.avgFusedConfidence == null ? "--" : `${row.avgFusedConfidence}%`}
                </td>
                <td className="px-3 py-3">{row.visualConfidence}%</td>
                <td className="px-3 py-3">{row.thermalConfidence}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function StackedAlerts({
  alerts,
  onDismiss,
  onDismissAll,
}: {
  alerts: NonNullable<ReturnType<typeof mapRealtimeAlertToBannerData>>[];
  onDismiss: (alertId: string) => void;
  onDismissAll: () => void;
}) {
  const visibleAlerts = alerts.slice(0, 3);
  const hiddenAlertCount = Math.max(alerts.length - visibleAlerts.length, 0);

  return (
    <div className="space-y-3">
      <div className="space-y-0">
        {visibleAlerts.map((alert, index) => {
          const isTopAlert = index === 0;

          return (
            <AlertBanner
              key={alert.id}
              alert={alert}
              onDismiss={() => onDismiss(alert.id)}
              action={
                isTopAlert && alerts.length > 1 ? (
                  <button
                    type="button"
                    onClick={onDismissAll}
                    className="inline-flex items-center gap-1 rounded-md border border-black/10 bg-white/40 px-3 py-2 text-xs font-semibold uppercase tracking-wide transition-colors hover:bg-white/70 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
                  >
                    <X className="size-3.5" aria-hidden="true" />
                    Clear all
                  </button>
                ) : null
              }
              className={
                index === 0
                  ? "relative z-30"
                  : index === 1
                    ? "-mt-[4.5rem] relative z-20"
                    : "-mt-20 relative z-10"
              }
            />
          );
        })}
      </div>
      {hiddenAlertCount > 0 ? (
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          +{hiddenAlertCount} more alert{hiddenAlertCount === 1 ? "" : "s"} queued
        </p>
      ) : null}
    </div>
  );
}

function SystemStatusPanel({ services }: { services: DashboardSystemStatusItem[] }) {
  const statusClasses: Record<DashboardSystemStatus, string> = {
    Connected: "bg-emerald-500",
    Unstable: "bg-amber-400",
    Disconnected: "bg-rose-500",
  };

  const statusTextClasses: Record<DashboardSystemStatus, string> = {
    Connected: "text-emerald-700",
    Unstable: "text-amber-700",
    Disconnected: "text-rose-700",
  };

  const liveServices = services.filter((service) => service.source === "live");
  const placeholderServices = services.filter((service) => service.source === "mock");

  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">System Status</h2>
      <div className="mt-4 space-y-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
            Live Signals
          </p>
          <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-300">
            {liveServices.map((service) => (
              <li key={service.name} className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className={`size-3 rounded-full ${statusClasses[service.status]}`} />
                  <span>{service.name}</span>
                </div>
                <span className={`text-sm font-semibold ${statusTextClasses[service.status]}`}>
                  {service.status}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {placeholderServices.length > 0 ? (
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Placeholder Services
            </p>
            <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-300">
              {placeholderServices.map((service) => (
                <li key={service.name} className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`size-3 rounded-full ${statusClasses[service.status]}`} />
                    <span>{service.name}</span>
                  </div>
                  <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    Mock
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function streamFps(stream: { fps?: number | null } | undefined, fallback: string) {
  return stream?.fps ? String(stream.fps) : fallback;
}

export default function LiveFeedPage() {
  const { visualStream, thermalStream, isLoading, errorMessage, refresh } = useLiveStreams();
  const { alerts: realtimeAlerts, dismissAlert, dismissAllAlerts } = useRealtimeAlerts();
  const { summary, recentIncidents, services } = useDashboardDetectionState({
    visualStream,
    thermalStream,
  });

  const visibleAlerts = realtimeAlerts
    .map(mapRealtimeAlertToBannerData)
    .filter((alert): alert is NonNullable<typeof alert> => alert !== null);

  return (
    <DashboardShell>
      <div className="grid gap-4 lg:grid-cols-5">
        <div className="space-y-4 lg:col-span-4">
          {visibleAlerts.length > 0 ? (
            <StackedAlerts
              alerts={visibleAlerts}
              onDismiss={dismissAlert}
              onDismissAll={dismissAllAlerts}
            />
          ) : null}

          {errorMessage ? (
            <StreamsMetaErrorBanner errorMessage={errorMessage} onRetry={() => void refresh()} />
          ) : null}

          <div className="grid gap-4 xl:grid-cols-2">
            <VideoPanel
              title="Visual - RGB"
              fps={streamFps(visualStream, "15")}
              resolution={
                isLoading && !visualStream
                  ? "1280x720 • RGB • LOADING"
                  : buildVideoSubLabel(visualStream, "1280x720 • RGB")
              }
            >
              <StreamVideo stream={visualStream} title="Visual RGB stream" />
            </VideoPanel>
            <VideoPanel
              title="Thermal - IR"
              fps={streamFps(thermalStream, "15")}
              resolution={
                isLoading && !thermalStream
                  ? "160x120 • IR • LOADING"
                  : buildVideoSubLabel(thermalStream, "160x120 • IR")
              }
            >
              <StreamVideo stream={thermalStream} title="Thermal IR stream" />
            </VideoPanel>
          </div>

          <RecentIncidentsTable incidents={recentIncidents} />
        </div>

        <div className="space-y-4">
          <ConfidencePanel summary={summary} />
          <SystemStatusPanel services={services} />
        </div>
      </div>
    </DashboardShell>
  );
}
