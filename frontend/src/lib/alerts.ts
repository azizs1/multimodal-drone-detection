export type AlertSeverity = "info" | "warning" | "critical";

export type AlertSource = "fusion" | "detection" | "system";

export type AlertConfidenceBand = "low" | "medium" | "high";

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

export type FusionAlertLike = {
  incidentId: string;
  decision: "drone" | "none";
  fusedConfidence: number;
  confidenceBand: AlertConfidenceBand;
  gatingReason: string;
  timestamp: number;
  streamName?: string;
};

export function mapFusionAlertToBannerData(alert: FusionAlertLike): AlertBannerData | null {
  if (alert.decision !== "drone") {
    return null;
  }

  return {
    id: alert.incidentId,
    title: "Drone detected",
    message: `Fusion confidence exceeded alert threshold (${alert.gatingReason}).`,
    severity: alert.confidenceBand === "high" ? "critical" : "warning",
    source: "fusion",
    occurredAt: new Date(alert.timestamp * 1000).toISOString(),
    confidence: alert.fusedConfidence,
    confidenceBand: alert.confidenceBand,
    streamName: alert.streamName,
    dismissible: true,
  };
}
