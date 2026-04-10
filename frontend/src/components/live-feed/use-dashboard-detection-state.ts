"use client";

import { useEffect, useMemo, useState } from "react";
import { buildServiceItems } from "@/components/live-feed/live-feed-state.mjs";
import {
  mapIncidentToDashboardRow,
  mapIncidentToDashboardSummary,
  type DashboardDetectionSummary,
  type DashboardIncidentRow,
  type DashboardSystemStatusItem,
} from "@/lib/dashboard-detection.mjs";
import { getIncidents, type IncidentResponse } from "@/lib/api/incidents";

const BASE_SYSTEM_STATUS: DashboardSystemStatusItem[] = [
  { name: "Jetson Nano", status: "Unstable", source: "mock" },
  { name: "Backend", status: "Connected", source: "mock" },
  { name: "WebSocket", status: "Disconnected", source: "mock" },
];

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
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);

  useEffect(() => {
    let isMounted = true;

    const loadIncidents = async () => {
      try {
        const data = await getIncidents();
        if (!isMounted) {
          return;
        }

        setIncidents(data);
      } catch {
        if (!isMounted) {
          return;
        }

        setIncidents([]);
      }
    };

    void loadIncidents();

    return () => {
      isMounted = false;
    };
  }, []);

  const summary = useMemo(
    () => mapIncidentToDashboardSummary(incidents[0]),
    [incidents],
  );

  const recentIncidents = useMemo(
    () => incidents.slice(0, 5).map(mapIncidentToDashboardRow),
    [incidents],
  );

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
    summary,
    recentIncidents,
    services,
  };
}
