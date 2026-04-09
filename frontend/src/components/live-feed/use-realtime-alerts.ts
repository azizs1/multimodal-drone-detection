"use client";

import { useEffect, useMemo, useState } from "react";
import {
  normalizeRealtimeAlertEvent,
  type IncomingRealtimeAlertPayload,
  type RealtimeAlertEvent,
} from "@/lib/alerts";

export type RealtimeAlertConnectionState =
  | "mock"
  | "connecting"
  | "connected"
  | "disconnected"
  | "error";

const MOCK_ALERT_EVENTS: RealtimeAlertEvent[] = [
  {
    incidentId: "mock-fusion-alert-001",
    decision: "drone",
    fusedConfidence: 0.82,
    confidenceBand: "high",
    gatingReason: "rgb+thermal",
    timestamp: Date.now() / 1000,
    streamName: "visual",
  },
  {
    incidentId: "mock-fusion-alert-002",
    decision: "drone",
    fusedConfidence: 0.91,
    confidenceBand: "high",
    gatingReason: "thermal confirmation",
    timestamp: Date.now() / 1000 + 12,
    streamName: "thermal",
  },
];

function buildMockAlertEvent(index: number): RealtimeAlertEvent {
  const seed = MOCK_ALERT_EVENTS[index % MOCK_ALERT_EVENTS.length];

  return {
    ...seed,
    incidentId: `${seed.incidentId}-${index + 1}`,
    timestamp: Date.now() / 1000,
  };
}

export type UseRealtimeAlertsResult = {
  activeAlertEvent: RealtimeAlertEvent | null;
  connectionState: RealtimeAlertConnectionState;
  dismissAlert: () => void;
  triggerMockAlert: () => void;
};

export function useRealtimeAlerts(): UseRealtimeAlertsResult {
  const [activeAlertEvent, setActiveAlertEvent] = useState<RealtimeAlertEvent | null>(null);
  const [mockAlertIndex, setMockAlertIndex] = useState(1);
  const [connectionState, setConnectionState] = useState<RealtimeAlertConnectionState>("connecting");

  const websocketUrl = useMemo(() => {
    if (typeof window === "undefined") {
      return null;
    }

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    const endpoint = new URL("/incidents/alert", apiBaseUrl);
    endpoint.protocol = endpoint.protocol === "https:" ? "wss:" : "ws:";
    return endpoint.toString();
  }, []);

  useEffect(() => {
    if (!websocketUrl) {
      return undefined;
    }

    const socket = new WebSocket(websocketUrl);

    socket.onopen = () => {
      setConnectionState("connected");
    };

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as IncomingRealtimeAlertPayload;
      setActiveAlertEvent(normalizeRealtimeAlertEvent(payload));
    };

    socket.onerror = () => {
      setConnectionState("error");
    };

    socket.onclose = () => {
      setConnectionState("disconnected");
    };

    return () => {
      socket.close();
    };
  }, [websocketUrl]);

  // TODO: Add reconnect/backoff handling and malformed payload protection so
  // transient websocket failures do not require a page refresh.

  return {
    activeAlertEvent,
    connectionState,
    dismissAlert: () => setActiveAlertEvent(null),
    triggerMockAlert: () => {
      setActiveAlertEvent(buildMockAlertEvent(mockAlertIndex));
      setMockAlertIndex((current) => current + 1);
    },
  };
}
