export type DashboardIncidentStatus = "Confirmed" | "Pending" | "False Positive";

export type DashboardDetectionSummary = {
  fusedConfidence: number;
  distanceFt: number;
  visualConfidence: number;
  thermalConfidence: number;
};

export type DashboardIncidentRow = {
  id: string;
  occurredAt: string;
  fusedConfidence: number;
  distanceFt: number;
  status: DashboardIncidentStatus;
};

export type DashboardSystemStatus = "Connected" | "Unstable" | "Disconnected";

export type DashboardSystemStatusItem = {
  name: string;
  status: DashboardSystemStatus;
  source: "live" | "mock";
};

export const MOCK_DASHBOARD_INCIDENT_ROWS: DashboardIncidentRow[] = [
  { id: "#001", occurredAt: "14:32:07", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
  { id: "#002", occurredAt: "14:33:16", fusedConfidence: 92, distanceFt: 15, status: "Confirmed" },
  { id: "#003", occurredAt: "14:35:44", fusedConfidence: 93, distanceFt: 14, status: "Confirmed" },
  { id: "#004", occurredAt: "14:37:09", fusedConfidence: 95, distanceFt: 13, status: "Confirmed" },
  { id: "#005", occurredAt: "14:40:51", fusedConfidence: 94, distanceFt: 14, status: "Confirmed" },
];
