import { format } from "date-fns";

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
 *   decision: string;
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
    id: incident.incident_id,
    occurredAt: format(new Date(incident.detected_at), "MMM dd, h:mm a"),
    fusedConfidence: Math.round(incident.fused_confidence * 100),
    visualConfidence: Math.round((incident.per_modality_scores.rgb ?? 0) * 100),
    thermalConfidence: Math.round((incident.per_modality_scores.thermal ?? 0) * 100),
    decision: incident.decision,
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
