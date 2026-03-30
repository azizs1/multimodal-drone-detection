/**
 * @typedef {"Confirmed" | "Pending" | "False Positive"} DashboardIncidentStatus
 */

/**
 * @typedef {{
 *   fusedConfidence: number;
 *   distanceFt: number;
 *   visualConfidence: number;
 *   thermalConfidence: number;
 * }} DashboardDetectionSummary
 */

/**
 * @typedef {{
 *   id: string;
 *   occurredAt: string;
 *   fusedConfidence: number;
 *   distanceFt: number;
 *   status: DashboardIncidentStatus;
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

/** @type {DashboardIncidentRow[]} */
export const MOCK_DASHBOARD_INCIDENT_ROWS = [
  { id: "#001", occurredAt: "14:32:07", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
  { id: "#002", occurredAt: "14:33:16", fusedConfidence: 92, distanceFt: 15, status: "Confirmed" },
  { id: "#003", occurredAt: "14:35:44", fusedConfidence: 93, distanceFt: 14, status: "Confirmed" },
  { id: "#004", occurredAt: "14:37:09", fusedConfidence: 95, distanceFt: 13, status: "Confirmed" },
  { id: "#005", occurredAt: "14:40:51", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
];
