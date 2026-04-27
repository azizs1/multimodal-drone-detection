"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Cpu, Database, RadioTower, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Badge } from "@/components/ui/badge";
import { getHealthReady, type ReadinessCheckResponse } from "@/lib/api/health";
import { getStreams, type StreamInfo } from "@/lib/api/streams";

type ApiStatus = "checking" | "connected" | "degraded" | "offline";

const DETECTION_CONFIG = [
  { label: "Alert threshold", value: "75%", detail: "Fused confidence required before a drone alert is emitted." },
  { label: "Hold threshold", value: "55%", detail: "Scores below alert level remain buffered for follow-up frames." },
  { label: "RGB gate", value: "45%", detail: "Minimum RGB confidence used by the fusion engine." },
  { label: "Thermal gate", value: "35%", detail: "Minimum thermal confidence used by the fusion engine." },
];

const MODEL_INFO = [
  { label: "Fusion strategy", value: "Weighted late fusion" },
  { label: "RGB weight", value: "60%" },
  { label: "Thermal weight", value: "40%" },
  { label: "Debounce window", value: "2 frames / 1000 ms" },
];

function formatTimestamp(timestamp?: number) {
  if (!timestamp) {
    return "Not available";
  }

  return new Date(timestamp * 1000).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getStatusBadge(status: ApiStatus) {
  if (status === "connected") {
    return <Badge className="border-transparent bg-emerald-100 text-emerald-700">API connected</Badge>;
  }

  if (status === "degraded") {
    return <Badge className="border-transparent bg-amber-100 text-amber-700">API degraded</Badge>;
  }

  if (status === "offline") {
    return <Badge className="border-transparent bg-rose-100 text-rose-700">API offline</Badge>;
  }

  return <Badge className="border-transparent bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-100">Checking API</Badge>;
}

function InfoCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof ShieldCheck;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-start gap-3">
        <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-sm bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300">
          <Icon className="size-5" aria-hidden="true" />
        </span>
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
          <p className="mt-1 text-2xl font-bold text-slate-800 dark:text-slate-100">{value}</p>
          <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">{detail}</p>
        </div>
      </div>
    </article>
  );
}

export default function SystemInfoPage() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [readiness, setReadiness] = useState<ReadinessCheckResponse | null>(null);
  const [streams, setStreams] = useState<StreamInfo[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function refreshSystemStatus() {
      try {
        const [readyResponse, streamsResponse] = await Promise.all([getHealthReady(), getStreams()]);

        if (!isMounted) {
          return;
        }

        setReadiness(readyResponse);
        setStreams(streamsResponse.streams);
        setApiStatus(readyResponse.status === "ready" ? "connected" : "degraded");
      } catch {
        if (isMounted) {
          setApiStatus("offline");
        }
      }
    }

    refreshSystemStatus();

    return () => {
      isMounted = false;
    };
  }, []);

  const activeStreamCount = useMemo(
    () => streams.filter((stream) => stream.status === "active").length,
    [streams],
  );

  return (
    <DashboardShell>
      <section className="space-y-4">
        <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-xl font-semibold text-slate-800 dark:text-slate-100">System Info</h1>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500 dark:text-slate-400">
                Read-only view of backend-managed detection configuration. Detection parameters are controlled by the fusion service, not by dashboard users.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-transparent bg-cyan-100 text-cyan-700">Backend managed</Badge>
              {getStatusBadge(apiStatus)}
            </div>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <InfoCard
            icon={ShieldCheck}
            label="Detection mode"
            value="Automatic"
            detail="The dashboard reports fused decisions from the backend pipeline."
          />
          <InfoCard
            icon={RadioTower}
            label="Input modalities"
            value="RGB + Thermal"
            detail={`${activeStreamCount}/${streams.length || 2} stream sources currently report active metadata.`}
          />
          <InfoCard
            icon={Activity}
            label="Last readiness check"
            value={formatTimestamp(readiness?.timestamp)}
            detail={readiness?.reason ?? "Backend readiness endpoint controls this status."}
          />
        </div>

        <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="size-4 text-cyan-600 dark:text-cyan-300" aria-hidden="true" />
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Detection Thresholds
              </h2>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {DETECTION_CONFIG.map((item) => (
                <div key={item.label} className="rounded-sm border border-slate-200 bg-slate-100 p-3 dark:border-slate-700 dark:bg-slate-800">
                  <div className="flex items-baseline justify-between gap-3">
                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{item.label}</p>
                    <p className="text-lg font-bold text-cyan-600 dark:text-cyan-300">{item.value}</p>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-slate-500 dark:text-slate-400">{item.detail}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2">
              <Cpu className="size-4 text-cyan-600 dark:text-cyan-300" aria-hidden="true" />
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Fusion Model
              </h2>
            </div>
            <dl className="mt-4 divide-y divide-slate-200 text-sm dark:divide-slate-800">
              {MODEL_INFO.map((item) => (
                <div key={item.label} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0">
                  <dt className="text-slate-500 dark:text-slate-400">{item.label}</dt>
                  <dd className="font-semibold text-slate-800 dark:text-slate-100">{item.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        <section className="rounded-sm border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2">
            <Database className="size-4 text-cyan-600 dark:text-cyan-300" aria-hidden="true" />
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Stream Sources
            </h2>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="text-slate-500 dark:text-slate-400">
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="px-3 py-3 font-semibold">Source</th>
                  <th className="px-3 py-3 font-semibold">Description</th>
                  <th className="px-3 py-3 font-semibold">Status</th>
                  <th className="px-3 py-3 font-semibold">HLS endpoint</th>
                </tr>
              </thead>
              <tbody>
                {(streams.length > 0 ? streams : [
                  { name: "visual", description: "RGB video stream", hls_url: "Backend metadata unavailable", status: "inactive" },
                  { name: "thermal", description: "Thermal video stream", hls_url: "Backend metadata unavailable", status: "inactive" },
                ]).map((stream) => (
                  <tr key={stream.name} className="border-b border-slate-200/80 dark:border-slate-800">
                    <td className="px-3 py-3 font-semibold text-slate-800 dark:text-slate-100">{stream.name}</td>
                    <td className="px-3 py-3">{stream.description}</td>
                    <td className="px-3 py-3">
                      <span className="inline-flex rounded-full bg-slate-200 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                        {stream.status}
                      </span>
                    </td>
                    <td className="max-w-[24rem] truncate px-3 py-3">{stream.hls_url}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </DashboardShell>
  );
}
