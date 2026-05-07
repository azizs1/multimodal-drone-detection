"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { buildServiceItems, deriveJetsonStatus } from "@/components/live-feed/live-feed-state.mjs";
import {
  mapIncidentToDashboardRow,
  mapIncidentToDashboardSummary,
  type DashboardSystemStatus,
  type DashboardDetectionSummary,
  type DashboardIncidentRow,
  type DashboardSystemStatusItem,
} from "@/lib/dashboard-detection.mjs";
import { getIncidents, type IncidentResponse } from "@/lib/api/incidents";
import { getHealthReady } from "@/lib/api/health";

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
  const [backendStatus, setBackendStatus] = useState<DashboardSystemStatus>("Unstable");
  const [websocketStatus, setWebsocketStatus] = useState<DashboardSystemStatus>("Unstable");
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

  // Remaining live-feed gap after this integration pass:
  // - The dashboard currently refreshes incidents by refetching the list when a
  //   websocket alert arrives; if a richer dashboard-specific stream is added
  //   later, this hook should switch to consuming that directly.

  const summary = useMemo(
    () => mapIncidentToDashboardSummary(incidents[0]),
    [incidents],
  );

  const recentIncidents = useMemo(
    () => incidents.slice(0, 5).map(mapIncidentToDashboardRow),
    [incidents],
  );

  useEffect(() => {
    let isMounted = true;

    const loadBackendHealth = async () => {
      try {
        const readiness = await getHealthReady();
        if (!isMounted) {
          return;
        }

        setBackendStatus(readiness.status === "ready" ? "Connected" : "Unstable");
      } catch {
        if (!isMounted) {
          return;
        }

        setBackendStatus("Disconnected");
      }
    };

    void loadBackendHealth();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return undefined;
    }

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    const endpoint = new URL("/incidents/alert", apiBaseUrl);
    endpoint.protocol = endpoint.protocol === "https:" ? "wss:" : "ws:";

    let socket: WebSocket | null = null;
    let isUnmounted = false;

    const clearReconnectTimeout = () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    const connect = () => {
      if (isUnmounted) {
        return;
      }

      setWebsocketStatus("Unstable");
      socket = new WebSocket(endpoint.toString());

      socket.onopen = () => {
        clearReconnectTimeout();
        setWebsocketStatus("Connected");
      };

      socket.onmessage = () => {
        void getIncidents()
          .then((data) => {
            if (!isUnmounted) {
              setIncidents(data);
            }
          })
          .catch(() => {
            if (!isUnmounted) {
              setIncidents([]);
            }
          });
      };

      socket.onerror = () => {
        setWebsocketStatus("Unstable");
      };

      socket.onclose = () => {
        if (isUnmounted) {
          return;
        }

        setWebsocketStatus("Disconnected");
        clearReconnectTimeout();
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 1500);
      };
    };

    connect();

    return () => {
      isUnmounted = true;
      clearReconnectTimeout();

      if (socket) {
        socket.close();
      }
    };
  }, []);

  const services = useMemo(() => {
    const liveServices: DashboardSystemStatusItem[] = buildServiceItems(
      visualStream,
      thermalStream,
      [],
    ).map((service) => ({
      ...service,
      source: "live",
    }));

    const serviceHealthItems: DashboardSystemStatusItem[] = [
      { name: "Jetson Nano", status: deriveJetsonStatus(visualStream, thermalStream), source: "live" },
      { name: "Backend", status: backendStatus, source: "live" },
      { name: "WebSocket", status: websocketStatus, source: "live" },
    ];

    return [...liveServices, ...serviceHealthItems];
  }, [backendStatus, thermalStream, visualStream, websocketStatus]);

  return {
    summary,
    recentIncidents,
    services,
  };
}
