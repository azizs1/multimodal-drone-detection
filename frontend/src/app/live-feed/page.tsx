"use client";

import { DashboardShell } from "@/components/layout/dashboard-shell";
import { HlsVideoPlayer } from "@/components/live-feed/hls-video-player";
import { useLiveStreams } from "@/components/live-feed/use-live-streams";
import { VideoPanel } from "@/components/live-feed/video-panel";
import type { StreamInfo } from "@/lib/api/streams";

type IncidentRow = {
  id: string;
  time: string;
  fusedConfidence: number;
  distanceFt: number;
  status: "Confirmed";
};

const INCIDENT_ROWS: IncidentRow[] = [
  { id: "#001", time: "14:32:07", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
  { id: "#002", time: "14:33:16", fusedConfidence: 92, distanceFt: 15, status: "Confirmed" },
  { id: "#003", time: "14:35:44", fusedConfidence: 93, distanceFt: 14, status: "Confirmed" },
  { id: "#004", time: "14:37:09", fusedConfidence: 95, distanceFt: 13, status: "Confirmed" },
  { id: "#005", time: "14:40:51", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
];

type ServiceStatus = "Connected" | "Unstable" | "Disconnected";

type ServiceItem = {
  name: string;
  status: ServiceStatus;
};

const BASE_SYSTEM_STATUS: ServiceItem[] = [
  { name: "Jetson Nano", status: "Unstable" },
  { name: "Backend", status: "Connected" },
  { name: "WebSocket", status: "Disconnected" },
];

function toServiceStatus(status: StreamInfo["status"]): ServiceStatus {
  if (status === "active") {
    return "Connected";
  }
  if (status === "inactive") {
    return "Disconnected";
  }
  return "Unstable";
}

function buildVideoSubLabel(stream: StreamInfo | undefined, fallback: string): string {
  if (!stream) {
    return `${fallback} • Not available`;
  }

  return `${fallback} • ${stream.status.toUpperCase()}`;
}

function buildStreamPlaylistUrl(streamName: string): string {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return `${apiBaseUrl}/streams/${streamName}/hls/index.m3u8`;
}

function ConfidencePanel() {
  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Primary Metrics</p>
        <div className="mt-2 grid gap-3">
          <div className="rounded-md border border-cyan-100 bg-cyan-50/60 px-3 py-4 text-center dark:border-cyan-700/50 dark:bg-slate-800">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Fused Confidence</p>
            <p className="mt-1 text-4xl font-extrabold text-cyan-500 dark:text-cyan-400">94%</p>
          </div>

          <div className="rounded-md border border-cyan-100 bg-cyan-50/60 px-3 py-4 text-center dark:border-cyan-700/50 dark:bg-slate-800">
            <p className="text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">Distance</p>
            <p className="mt-1 text-4xl font-extrabold text-cyan-500 dark:text-cyan-400">~14ft</p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Secondary Metrics
        </p>
        <div className="mt-2 rounded-md border border-slate-200 bg-slate-100 p-3 text-center dark:border-slate-700 dark:bg-slate-800">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Visual Confidence</p>
              <p className="mt-1 text-3xl font-bold text-slate-400 dark:text-slate-300">92%</p>
            </div>
            <div>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Thermal Confidence</p>
              <p className="mt-1 text-3xl font-bold text-slate-400 dark:text-slate-300">89%</p>
            </div>
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

function RecentIncidentsTable() {
  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        Recent Incidents
      </h2>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] border-collapse text-left text-sm text-slate-600 dark:text-slate-300">
          <thead className="text-slate-500 dark:text-slate-400">
            <tr className="border-b border-slate-200 dark:border-slate-700">
              <th className="px-3 py-3 font-semibold">ID</th>
              <th className="px-3 py-3 font-semibold">Time</th>
              <th className="px-3 py-3 font-semibold">Fused Confidence</th>
              <th className="px-3 py-3 font-semibold">Distance</th>
              <th className="px-3 py-3 font-semibold">Status</th>
              <th className="px-3 py-3 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {INCIDENT_ROWS.map((row) => (
              <tr key={row.id + row.time} className="border-b border-slate-200/80 dark:border-slate-800">
                <td className="px-3 py-3">{row.id}</td>
                <td className="px-3 py-3">{row.time}</td>
                <td className="px-3 py-3">{row.fusedConfidence}%</td>
                <td className="px-3 py-3">~{row.distanceFt}ft</td>
                <td className="px-3 py-3">
                  <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300">
                    {row.status}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <button
                    type="button"
                    className="inline-flex items-center rounded-md border border-slate-300 bg-slate-100 px-4 py-1 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-1 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function SystemStatusPanel({ services }: { services: ServiceItem[] }) {
  const statusClasses: Record<ServiceStatus, string> = {
    Connected: "bg-emerald-500",
    Unstable: "bg-amber-400",
    Disconnected: "bg-rose-500",
  };

  const statusTextClasses: Record<ServiceStatus, string> = {
    Connected: "text-emerald-700",
    Unstable: "text-amber-700",
    Disconnected: "text-rose-700",
  };

  return (
    <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">System Status</h2>
      <ul className="mt-4 space-y-2 text-sm text-slate-700 dark:text-slate-300">
        {services.map((service) => (
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
    </section>
  );
}

export default function LiveFeedPage() {
  const { visualStream, thermalStream, isLoading, errorMessage, refresh } = useLiveStreams();

  const services: ServiceItem[] = [
    { name: "RGB Cam", status: visualStream ? toServiceStatus(visualStream.status) : "Disconnected" },
    { name: "Thermal Cam", status: thermalStream ? toServiceStatus(thermalStream.status) : "Disconnected" },
    ...BASE_SYSTEM_STATUS,
  ];

  return (
    <DashboardShell>
      <div className="grid gap-4 lg:grid-cols-5">
        <div className="space-y-4 lg:col-span-4">
          {errorMessage ? (
            <StreamsMetaErrorBanner errorMessage={errorMessage} onRetry={() => void refresh()} />
          ) : null}

          <div className="grid gap-4 xl:grid-cols-2">
            <VideoPanel
              title="Visual - RGB"
              fps="30"
              resolution={
                isLoading && !visualStream
                  ? "1920x1080 • RGB • LOADING"
                  : buildVideoSubLabel(visualStream, "1920x1080 • RGB")
              }
            >
              <HlsVideoPlayer
                title="Visual RGB stream"
                src={visualStream ? buildStreamPlaylistUrl(visualStream.name) : undefined}
              />
            </VideoPanel>
            <VideoPanel
              title="Thermal - IR"
              fps="30"
              resolution={
                isLoading && !thermalStream
                  ? "640x480 • IR • LOADING"
                  : buildVideoSubLabel(thermalStream, "640x480 • IR")
              }
            >
              <HlsVideoPlayer
                title="Thermal IR stream"
                src={thermalStream ? buildStreamPlaylistUrl(thermalStream.name) : undefined}
              />
            </VideoPanel>
          </div>

          <RecentIncidentsTable />
        </div>

        <div className="space-y-4">
          <ConfidencePanel />
          <SystemStatusPanel services={services} />
        </div>
      </div>
    </DashboardShell>
  );
}
