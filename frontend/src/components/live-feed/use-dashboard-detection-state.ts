"use client";

import { useMemo } from "react";
import { buildServiceItems } from "@/components/live-feed/live-feed-state.mjs";
import {
  MOCK_DASHBOARD_INCIDENT_ROWS,
  type DashboardDetectionSummary,
  type DashboardIncidentRow,
  type DashboardSystemStatusItem,
} from "@/lib/dashboard-detection.mjs";

const BASE_SYSTEM_STATUS: DashboardSystemStatusItem[] = [
  { name: "Jetson Nano", status: "Unstable", source: "mock" },
  { name: "Backend", status: "Connected", source: "mock" },
  { name: "WebSocket", status: "Disconnected", source: "mock" },
];

const MOCK_DASHBOARD_SUMMARY: DashboardDetectionSummary = {
  fusedConfidence: 94,
  distanceFt: 14,
  visualConfidence: 92,
  thermalConfidence: 89,
};

export type UseDashboardDetectionStateResult = {
  summary: DashboardDetectionSummary;
  recentIncidents: DashboardIncidentRow[];
  services: DashboardSystemStatusItem[];
};

export function useDashboardDetectionState({
  visualStream,
  thermalStream,
}: {
  visualStream?: { status: "active" | "inactive" | "error" };
  thermalStream?: { status: "active" | "inactive" | "error" };
}): UseDashboardDetectionStateResult {
  const services = useMemo(() => {
    const liveServices: DashboardSystemStatusItem[] = buildServiceItems(
      visualStream,
      thermalStream,
      [],
    ).map((service) => ({
      ...service,
      source: "live",
    }));

    return [...liveServices, ...BASE_SYSTEM_STATUS];
  }, [thermalStream, visualStream]);

  return {
    summary: MOCK_DASHBOARD_SUMMARY,
    recentIncidents: MOCK_DASHBOARD_INCIDENT_ROWS,
    services,
  };
}
