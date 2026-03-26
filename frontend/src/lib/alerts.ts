export type AlertSeverity = "info" | "warning" | "critical";

export type AlertSource = "fusion" | "detection" | "system";

export type AlertConfidenceBand = "low" | "medium" | "high";

export type RealtimeAlertDecision = "drone" | "none";

export type AlertBannerData = {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  source: AlertSource;
  occurredAt: string;
  confidence?: number;
  confidenceBand?: AlertConfidenceBand;
  streamName?: string;
  thumbnailUrl?: string;
  dismissible?: boolean;
};

export type RealtimeAlertEvent = {
  incidentId: string;
  decision: RealtimeAlertDecision;
  fusedConfidence: number;
  confidenceBand: AlertConfidenceBand;
  gatingReason: string;
  timestamp: number;
  streamName?: string;
};

export function mapRealtimeAlertSeverity(confidenceBand: AlertConfidenceBand): AlertSeverity {
  if (confidenceBand === "high") {
    return "critical";
  }

  if (confidenceBand === "medium") {
    return "warning";
  }

  return "info";
}

export function mapRealtimeAlertToBannerData(alert: RealtimeAlertEvent): AlertBannerData | null {
  if (alert.decision !== "drone") {
    return null;
  }

  const hasThresholdReason = alert.gatingReason.toLowerCase().includes("threshold");
  const message = hasThresholdReason
    ? `Fusion confidence exceeded alert threshold (${alert.gatingReason}).`
    : `Fusion decision flagged a drone event (${alert.gatingReason}).`;

  return {
    id: alert.incidentId,
    title: "Drone detected",
    message,
    severity: mapRealtimeAlertSeverity(alert.confidenceBand),
    source: "fusion",
    occurredAt: new Date(alert.timestamp * 1000).toISOString(),
    confidence: alert.fusedConfidence,
    confidenceBand: alert.confidenceBand,
    streamName: alert.streamName,
    dismissible: true,
  };
}

export function mapFusionAlertToBannerData(alert: RealtimeAlertEvent): AlertBannerData | null {
  return mapRealtimeAlertToBannerData(alert);
}
