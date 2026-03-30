export type IncidentLogStatus = "Confirmed" | "Pending" | "False Positive";

export type IncidentPanelStatus = IncidentLogStatus;

export type IncidentDetailPanelData = {
  id: string;
  timestamp: string;
  fusedConfidence: number;
  confidenceBand: "Low" | "Medium" | "High";
  decision: "Drone" | "No Drone" | "Review";
  status: IncidentPanelStatus;
  gatingReason: string;
  latencyMs: number;
  visualScore: number;
  thermalScore: number;
  rgbMediaLabel?: string;
  thermalMediaLabel?: string;
  thresholdLabel: string;
  objectsLabel: string;
};

export type IncidentLogRow = {
  id: string;
  timestamp: string;
  confidence: number;
  distanceFt: number;
  model: string;
  status: IncidentLogStatus;
};

export function mapIncidentRowToDetail(row: IncidentLogRow): IncidentDetailPanelData {
  // TODO: Replace this temporary adapter with the backend incident/fused payload
  // once the incident detail contract is finalized. The panel shape is already
  // aligned toward fused decision data, so this mapper is the intended seam.
  return {
    id: row.id,
    timestamp: row.timestamp,
    fusedConfidence: row.confidence,
    confidenceBand: row.confidence >= 90 ? "High" : row.confidence >= 80 ? "Medium" : "Low",
    decision:
      row.status === "False Positive" ? "No Drone" : row.status === "Pending" ? "Review" : "Drone",
    status: row.status,
    gatingReason:
      row.status === "False Positive"
        ? "Confidence did not hold after analyst review."
        : row.status === "Pending"
          ? "Awaiting additional thermal confirmation."
          : "Fusion threshold exceeded across available modalities.",
    latencyMs: 82 + (row.confidence % 9),
    visualScore: Math.max(0, Math.min(99, row.confidence - 2)),
    thermalScore: Math.max(0, Math.min(99, row.confidence - 5)),
    rgbMediaLabel: `RGB snapshot reference for ${row.id}`,
    thermalMediaLabel: `Thermal snapshot reference for ${row.id}`,
    thresholdLabel: "Confidence threshold and gating rules will be surfaced from the fused payload.",
    objectsLabel: "Detected object summaries and overlay metadata will be rendered here.",
  };
}
