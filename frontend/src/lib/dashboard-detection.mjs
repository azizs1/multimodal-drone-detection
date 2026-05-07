import { format } from "date-fns";
import { getIncidentDisplayId } from "./incidents.mjs";

/**
 * @typedef {"Confirmed" | "Pending" | "False Positive"} DashboardIncidentStatus
 */

/**
 * @typedef {{
 *   fusedConfidence: number;
 *   visualConfidence: number;
 *   thermalConfidence: number;
 * }} DashboardDetectionSummary
 */

/**
 * @typedef {{
 *   id: string;
  *   occurredAt: string;
  *   fusedConfidence: number;
 *   visualConfidence: number;
 *   thermalConfidence: number;
 *   avgFusedConfidence: number | null;
 *   frameCount: number | null;
 *   lastSeenAt: string | null;
 * }} DashboardIncidentRow
 */

/**
 * @typedef {"Connected" | "Unstable" | "Disconnected"} DashboardSystemStatus
 */

/**
 * @typedef {{
 *   name: string;
 *   status: DashboardSystemStatus;
 *   source: "live" | "mock";
 * }} DashboardSystemStatusItem
 */

/**
 * @param {import("./api/incidents").IncidentResponse} incident
 * @param {import("./api/incidents").IncidentResponse} incident
 * @returns {DashboardIncidentRow}
 */
export function mapIncidentToDashboardRow(incident) {
  return {
    id: getIncidentDisplayId(incident),
    occurredAt: format(new Date(incident.started_at ?? incident.detected_at), "MMM dd, h:mm a"),
    fusedConfidence: Math.round(incident.fused_confidence * 100),
    visualConfidence: Math.round((incident.per_modality_scores.rgb ?? 0) * 100),
    thermalConfidence: Math.round((incident.per_modality_scores.thermal ?? 0) * 100),
    avgFusedConfidence:
      typeof incident.avg_fused_confidence === "number"
        ? Math.round(incident.avg_fused_confidence * 100)
        : null,
    frameCount: typeof incident.frame_count === "number" ? incident.frame_count : null,
    lastSeenAt: incident.last_seen_at ?? null,
  };
}

/**
 * @param {import("./api/incidents").IncidentResponse | undefined} incident
 * @returns {DashboardDetectionSummary}
 */
export function mapIncidentToDashboardSummary(incident) {
  if (!incident) {
    return {
      fusedConfidence: 0,
      visualConfidence: 0,
      thermalConfidence: 0,
    };
  }

  return {
    fusedConfidence: Math.round(incident.fused_confidence * 100),
    visualConfidence: Math.round((incident.per_modality_scores.rgb ?? 0) * 100),
    thermalConfidence: Math.round((incident.per_modality_scores.thermal ?? 0) * 100),
  };
}
