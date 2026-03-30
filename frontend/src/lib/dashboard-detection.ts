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
