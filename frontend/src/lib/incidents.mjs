/**
 * @typedef {"Confirmed" | "Pending" | "False Positive"} IncidentLogStatus
 */

/**
 * @typedef {"drone" | "none"} IncidentDecision
 */

/**
 * @typedef {"low" | "medium" | "high"} IncidentConfidenceBand
 */

/**
 * @typedef {import("./api/incidents").IncidentResponse} IncidentResponse
 */

/**
 * @typedef {{
 *   id: string;
 *   timestamp: string;
 *   confidence: number;
 *   distanceFt: number;
 *   model: string;
 *   status: IncidentLogStatus;
 * }} IncidentLogRow
 */

/**
 * @typedef {{
 *   incidentId: string;
 *   detectedAt: string;
 *   decision: IncidentDecision;
 *   alertLevel: IncidentConfidenceBand;
 *   fusedConfidence: number;
 * }} IncidentTableRow
 */

/**
 * @typedef {IncidentLogStatus} IncidentPanelStatus
 */

/**
 * @typedef {{
 *   frameUrl: string | null;
 *   thumbnailUrl: string | null;
 * }} IncidentMediaReference
 */

/**
 * @typedef {{
 *   id: string;
 *   timestamp: string;
  *   fusedConfidence: number;
  *   confidenceBand: "Low" | "Medium" | "High";
 *   decision: "Drone" | "No Drone" | "Review";
 *   status: IncidentPanelStatus;
 *   gatingReason: string;
 *   latencyMs: number;
 *   visualScore: number;
 *   thermalScore: number;
 *   rgbMedia: IncidentMediaReference;
 *   thermalMedia: IncidentMediaReference;
 *   thresholdLabel: string;
 *   objectsLabel: string;
 * }} IncidentDetailPanelData
 */

/** @type {Record<IncidentPanelStatus, string>} */
export const INCIDENT_STATUS_BADGE_CLASSES = {
  Confirmed:
    "border-transparent bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
  Pending:
    "border-transparent bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300",
  "False Positive":
    "border-transparent bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300",
};

/**
 * @param {IncidentConfidenceBand} value
 * @returns {"Low" | "Medium" | "High"}
 */
function formatConfidenceBand(value) {
  if (value === "high") {
    return "High";
  }

  if (value === "medium") {
    return "Medium";
  }

  return "Low";
}

/**
 * @param {unknown} value
 * @returns {string}
 */
function toDisplayValue(value) {
  if (value == null) {
    return "--";
  }

  if (typeof value === "string") {
    return value.trim().length > 0 ? value : "--";
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

/**
 * @param {Record<string, number>} thresholds
 * @returns {string}
 */
function formatThresholdLabel(thresholds) {
  const entries = Object.entries(thresholds ?? {});

  if (entries.length === 0) {
    return "--";
  }

  return entries.map(([key, value]) => `${key}: ${value}`).join(", ");
}

/**
 * @param {unknown[]} objects
 * @returns {string}
 */
function formatObjectsLabel(objects) {
  if (!Array.isArray(objects) || objects.length === 0) {
    return "--";
  }

  return objects.map((object) => toDisplayValue(object)).join("\n");
}

/**
 * @param {unknown} mediaRef
 * @returns {IncidentMediaReference}
 */
function mapMediaReference(mediaRef) {
  if (!mediaRef || typeof mediaRef !== "object") {
    return {
      frameUrl: null,
      thumbnailUrl: null,
    };
  }

  return {
    frameUrl:
      typeof mediaRef.frame_uri === "string" && mediaRef.frame_uri.trim().length > 0
        ? mediaRef.frame_uri
        : null,
    thumbnailUrl:
      typeof mediaRef.thumbnail_uri === "string" && mediaRef.thumbnail_uri.trim().length > 0
        ? mediaRef.thumbnail_uri
        : null,
  };
}

/**
 * @param {IncidentResponse} incident
 * @returns {IncidentTableRow}
 */
export function mapIncidentResponseToRow(incident) {
  return {
    incidentId: incident.incident_id,
    detectedAt: incident.detected_at,
    decision: incident.decision,
    alertLevel: incident.alert_level,
    fusedConfidence: incident.fused_confidence,
  };
}

/**
 * @param {IncidentResponse} incident
 * @returns {IncidentDetailPanelData}
 */
export function mapIncidentResponseToDetail(incident) {
  return {
    id: incident.incident_id,
    timestamp: incident.detected_at,
    fusedConfidence: incident.fused_confidence,
    confidenceBand: formatConfidenceBand(incident.confidence_band),
    decision: incident.decision === "drone" ? "Drone" : "No Drone",
    status: incident.is_confirmed ? "Confirmed" : "Pending",
    gatingReason: toDisplayValue(incident.gating_reason),
    latencyMs: incident.latency_ms,
    visualScore: incident.per_modality_scores.rgb ?? 0,
    thermalScore: incident.per_modality_scores.thermal ?? 0,
    rgbMedia: mapMediaReference(incident.media?.rgb),
    thermalMedia: mapMediaReference(incident.media?.thermal),
    thresholdLabel: formatThresholdLabel(incident.thresholds),
    objectsLabel: formatObjectsLabel(incident.objects),
  };
}

/**
 * @param {IncidentLogRow} row
 * @returns {IncidentDetailPanelData}
 */
export function mapIncidentRowToDetail(row) {
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
    rgbMedia: {
      frameUrl: null,
      thumbnailUrl: null,
    },
    thermalMedia: {
      frameUrl: null,
      thumbnailUrl: null,
    },
    thresholdLabel: "Confidence threshold and gating rules will be surfaced from the fused payload.",
    objectsLabel: "Detected object summaries and overlay metadata will be rendered here.",
  };
}
