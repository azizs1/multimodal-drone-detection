"use client";

import { useState } from "react";
import { type RealtimeAlertEvent } from "@/lib/alerts";

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
  const [activeAlertEvent, setActiveAlertEvent] = useState<RealtimeAlertEvent | null>(
    buildMockAlertEvent(0),
  );
  const [mockAlertIndex, setMockAlertIndex] = useState(1);

  // TODO: Replace mock state with websocket-driven alerts once the backend
  // finalizes the realtime event contract for fused alert payloads.
  //
  // Expected follow-up shape:
  // 1. Open websocket connection in an effect on mount.
  // 2. Parse incoming JSON payloads into RealtimeAlertEvent.
  // 3. Set activeAlertEvent when a valid alert arrives.
  // 4. Update connectionState from mock to connected/disconnected/error.

  return {
    activeAlertEvent,
    connectionState: "mock",
    dismissAlert: () => setActiveAlertEvent(null),
    triggerMockAlert: () => {
      setActiveAlertEvent(buildMockAlertEvent(mockAlertIndex));
      setMockAlertIndex((current) => current + 1);
    },
  };
}
