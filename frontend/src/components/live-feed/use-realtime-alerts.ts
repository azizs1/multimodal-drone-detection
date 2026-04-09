"use client";

import { useEffect, useMemo, useRef, useState } from "react";
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

export type UseRealtimeAlertsResult = {
  activeAlertEvent: RealtimeAlertEvent | null;
  connectionState: RealtimeAlertConnectionState;
  dismissAlert: () => void;
};

function isIncomingRealtimeAlertPayload(value: unknown): value is IncomingRealtimeAlertPayload {
  if (!value || typeof value !== "object") {
    return false;
  }

  const payload = value as Record<string, unknown>;

  return (
    typeof payload.incident_id === "string" &&
    (payload.decision === "drone" || payload.decision === "none") &&
    typeof payload.fused_confidence === "number" &&
    (payload.confidence_band === "low" ||
      payload.confidence_band === "medium" ||
      payload.confidence_band === "high") &&
    typeof payload.gating_reason === "string" &&
    (payload.timestamp === undefined || typeof payload.timestamp === "number")
  );
}

export function useRealtimeAlerts(): UseRealtimeAlertsResult {
  const [activeAlertEvent, setActiveAlertEvent] = useState<RealtimeAlertEvent | null>(null);
  const [connectionState, setConnectionState] = useState<RealtimeAlertConnectionState>("connecting");
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

      setConnectionState("connecting");
      socket = new WebSocket(websocketUrl);

      socket.onopen = () => {
        clearReconnectTimeout();
        setConnectionState("connected");
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as unknown;

          if (!isIncomingRealtimeAlertPayload(payload)) {
            return;
          }

          setActiveAlertEvent(normalizeRealtimeAlertEvent(payload));
        } catch {
          setConnectionState("error");
        }
      };

      socket.onerror = () => {
        setConnectionState("error");
      };

      socket.onclose = () => {
        if (isUnmounted) {
          return;
        }

        setConnectionState("disconnected");
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
  }, [websocketUrl]);

  // TODO: If the dashboard starts consuming this state too, move the websocket
  // connection into a shared realtime incident/alert adapter to avoid duplicate
  // live subscriptions across components.

  return {
    activeAlertEvent,
    connectionState,
    dismissAlert: () => setActiveAlertEvent(null),
  };
}
