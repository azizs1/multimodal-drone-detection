import test from "node:test";
import assert from "node:assert/strict";
import {
  mapIncidentResponseToDetail,
  mapIncidentResponseToRow,
} from "./incidents.mjs";

test("mapIncidentResponseToRow returns the API-backed incident table fields", () => {
  const row = mapIncidentResponseToRow({
    id: "2f963c85-71de-4d87-b84a-d07cfed3fe0e",
    incident_id: "INC-014",
    detected_at: "2026-02-19T14:32:07Z",
    source_timestamp: 1771511527,
    has_drone: true,
    decision: "drone",
    confidence_band: "high",
    alert_level: "high",
    is_confirmed: true,
    fused_confidence: 94,
    stream_name: "fusion",
    primary_frame_url: "https://example.com/frame.jpg",
    primary_thumbnail_url: "https://example.com/thumb.jpg",
    per_modality_scores: {
      rgb: 92,
      thermal: 89,
    },
    thresholds: {
      drone: 0.85,
      thermal: 0.6,
    },
    gating_reason: "Fusion threshold exceeded.",
    latency_ms: 86,
    evidence: {
      visual_bbox: [12, 20, 60, 90],
    },
    media: {
      rgb_frame_url: "https://example.com/rgb.jpg",
      thermal_frame_url: "https://example.com/thermal.jpg",
    },
    objects: [{ label: "drone", confidence: 0.94 }],
    created_at: "2026-02-19T14:32:08Z",
    updated_at: "2026-02-19T14:32:08Z",
  });

  assert.deepEqual(row, {
    incidentId: "INC-014",
    detectedAt: "2026-02-19T14:32:07Z",
    decision: "drone",
    alertLevel: "high",
    fusedConfidence: 94,
  });
});

test("mapIncidentResponseToDetail maps API incidents into the detail panel shape", () => {
  const detail = mapIncidentResponseToDetail({
    id: "2f963c85-71de-4d87-b84a-d07cfed3fe0e",
    incident_id: "INC-014",
    detected_at: "2026-02-19T14:32:07Z",
    source_timestamp: 1771511527,
    has_drone: true,
    decision: "drone",
    confidence_band: "high",
    alert_level: "high",
    is_confirmed: true,
    fused_confidence: 94,
    stream_name: "fusion",
    primary_frame_url: "https://example.com/frame.jpg",
    primary_thumbnail_url: "https://example.com/thumb.jpg",
    per_modality_scores: {
      rgb: 92,
      thermal: 89,
    },
    thresholds: {
      drone: 0.85,
      thermal: 0.6,
    },
    gating_reason: "Fusion threshold exceeded.",
    latency_ms: 86,
    evidence: {
      visual_bbox: [12, 20, 60, 90],
    },
    media: {
      rgb_frame_url: "https://example.com/rgb.jpg",
      thermal_frame_url: "https://example.com/thermal.jpg",
    },
    objects: [{ label: "drone", confidence: 0.94 }],
    created_at: "2026-02-19T14:32:08Z",
    updated_at: "2026-02-19T14:32:08Z",
  });

  assert.deepEqual(detail, {
    id: "INC-014",
    timestamp: "2026-02-19T14:32:07Z",
    fusedConfidence: 94,
    confidenceBand: "High",
    decision: "Drone",
    status: "Confirmed",
    gatingReason: "Fusion threshold exceeded.",
    latencyMs: 86,
    visualScore: 92,
    thermalScore: 89,
    rgbMediaLabel: "https://example.com/rgb.jpg",
    thermalMediaLabel: "https://example.com/thermal.jpg",
    thresholdLabel: "drone: 0.85, thermal: 0.6",
    objectsLabel: '{\n  "label": "drone",\n  "confidence": 0.94\n}',
  });
});

test("mapIncidentResponseToDetail falls back cleanly when optional incident fields are missing", () => {
  const detail = mapIncidentResponseToDetail({
    id: "70d88f9e-f2db-4f01-bda0-763ff0e1ad34",
    incident_id: "INC-015",
    detected_at: "2026-02-19T14:36:11Z",
    source_timestamp: 1771511771,
    has_drone: false,
    decision: "none",
    confidence_band: "low",
    alert_level: "low",
    is_confirmed: false,
    fused_confidence: 72,
    stream_name: "fusion",
    primary_frame_url: null,
    primary_thumbnail_url: null,
    per_modality_scores: {},
    thresholds: {},
    gating_reason: "",
    latency_ms: 91,
    evidence: {},
    media: {},
    objects: [],
    created_at: "2026-02-19T14:36:12Z",
    updated_at: "2026-02-19T14:36:12Z",
  });

  assert.equal(detail.decision, "No Drone");
  assert.equal(detail.confidenceBand, "Low");
  assert.equal(detail.gatingReason, "--");
  assert.equal(detail.visualScore, 0);
  assert.equal(detail.thermalScore, 0);
  assert.equal(detail.rgbMediaLabel, "--");
  assert.equal(detail.thermalMediaLabel, "--");
  assert.equal(detail.thresholdLabel, "--");
  assert.equal(detail.objectsLabel, "--");
});
