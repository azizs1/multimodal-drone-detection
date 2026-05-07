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
    fused_confidence: 0.94,
    stream_name: "fusion",
    primary_frame_url: "https://example.com/frame.jpg",
    primary_thumbnail_url: "https://example.com/thumb.jpg",
    per_modality_scores: {
      rgb: 0.92,
      thermal: 0.89,
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
      rgb: {
        frame_uri: "https://example.com/rgb.jpg",
        thumbnail_uri: null,
      },
      thermal: {
        frame_uri: "https://example.com/thermal.jpg",
        thumbnail_uri: null,
      },
    },
    objects: [
      {
        object_id: "rgb-0",
        modality: "rgb",
        class_id: "drone",
        confidence: 0.94,
        bbox: [0.1, 0.2, 0.3, 0.4],
        timestamp: 1771511527,
      },
    ],
    created_at: "2026-02-19T14:32:08Z",
    updated_at: "2026-02-19T14:32:08Z",
  });

  assert.deepEqual(row, {
    incidentId: "INC-014",
    detectedAt: "2026-02-19T14:32:07Z",
    decision: "drone",
    alertLevel: "high",
    fusedConfidence: 0.94,
    avgFusedConfidence: null,
    frameCount: null,
    droneFrameCount: null,
    lastSeenAt: null,
    isAggregated: false,
  });
});

test("mapIncidentResponseToRow handles aggregated incident fields", () => {
  const row = mapIncidentResponseToRow({
    id: "2f963c85-71de-4d87-b84a-d07cfed3fe0e",
    aggregate_id: "agg-014",
    incident_id: "agg-014",
    detected_at: "2026-02-19T14:32:07Z",
    started_at: "2026-02-19T14:32:07Z",
    last_seen_at: "2026-02-19T14:32:11Z",
    ended_at: "2026-02-19T14:32:11Z",
    source_timestamp: 1771511531,
    has_drone: true,
    decision: "drone",
    confidence_band: "high",
    alert_level: "high",
    is_confirmed: true,
    fused_confidence: 0.94,
    avg_fused_confidence: 0.9,
    frame_count: 2,
    drone_frame_count: 2,
    representative_incident_id: "INC-014-B",
    raw_incident_ids: ["INC-014-A", "INC-014-B"],
    stream_name: "fusion",
    primary_frame_url: null,
    primary_thumbnail_url: null,
    per_modality_scores: {
      rgb: 0.92,
      thermal: 0.89,
    },
    thresholds: {
      alert: 0.75,
      hold: 0.55,
    },
    gating_reason: "rgb+thermal",
    latency_ms: 86,
    evidence: {
      rgb: null,
      thermal: null,
    },
    media: {
      rgb: null,
      thermal: null,
    },
    objects: [],
    created_at: "2026-02-19T14:32:08Z",
    updated_at: "2026-02-19T14:32:11Z",
  });

  assert.deepEqual(row, {
    incidentId: "agg-014",
    detectedAt: "2026-02-19T14:32:07Z",
    decision: "drone",
    alertLevel: "high",
    fusedConfidence: 0.94,
    avgFusedConfidence: 0.9,
    frameCount: 2,
    droneFrameCount: 2,
    lastSeenAt: "2026-02-19T14:32:11Z",
    isAggregated: true,
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
    fused_confidence: 0.94,
    stream_name: "fusion",
    primary_frame_url: "https://example.com/frame.jpg",
    primary_thumbnail_url: "https://example.com/thumb.jpg",
    per_modality_scores: {
      rgb: 0.92,
      thermal: 0.89,
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
      rgb: {
        frame_uri: "https://example.com/rgb.jpg",
        thumbnail_uri: null,
      },
      thermal: {
        frame_uri: "https://example.com/thermal.jpg",
        thumbnail_uri: null,
      },
    },
    objects: [
      {
        object_id: "rgb-0",
        modality: "rgb",
        class_id: "drone",
        confidence: 0.94,
        bbox: [0.1, 0.2, 0.3, 0.4],
        timestamp: 1771511527,
      },
    ],
    created_at: "2026-02-19T14:32:08Z",
    updated_at: "2026-02-19T14:32:08Z",
  });

  assert.deepEqual(detail, {
    id: "INC-014",
    timestamp: "2026-02-19T14:32:07Z",
    fusedConfidence: 0.94,
    confidenceBand: "High",
    decision: "Drone",
    status: "Confirmed",
    alertLevel: "High",
    gatingReason: "Fusion threshold exceeded.",
    latencyMs: 86,
    visualScore: 0.92,
    thermalScore: 0.89,
    rgbMedia: {
      frameUrl: "https://example.com/rgb.jpg",
      thumbnailUrl: null,
    },
    thermalMedia: {
      frameUrl: "https://example.com/thermal.jpg",
      thumbnailUrl: null,
    },
    thresholds: [
      { key: "drone", label: "Drone", value: 0.85 },
      { key: "thermal", label: "Thermal", value: 0.6 },
    ],
    objects: [
      {
        uniqueKey: "rgb-0::0",
        id: "rgb-0",
        modality: "rgb",
        classId: "drone",
        confidence: 0.94,
        bboxLabel: "0.10, 0.20, 0.30, 0.40",
      },
    ],
    isAggregated: false,
    startedAt: null,
    lastSeenAt: null,
    endedAt: null,
    avgFusedConfidence: null,
    frameCount: null,
    droneFrameCount: null,
    representativeIncidentId: null,
    rawIncidentIds: [],
  });
});

test("mapIncidentResponseToDetail exposes aggregate event metadata", () => {
  const detail = mapIncidentResponseToDetail({
    id: "2f963c85-71de-4d87-b84a-d07cfed3fe0e",
    aggregate_id: "agg-014",
    incident_id: "agg-014",
    detected_at: "2026-02-19T14:32:07Z",
    started_at: "2026-02-19T14:32:07Z",
    last_seen_at: "2026-02-19T14:32:11Z",
    ended_at: "2026-02-19T14:32:11Z",
    source_timestamp: 1771511531,
    has_drone: true,
    decision: "drone",
    confidence_band: "high",
    alert_level: "high",
    is_confirmed: true,
    fused_confidence: 0.94,
    avg_fused_confidence: 0.9,
    frame_count: 2,
    drone_frame_count: 2,
    representative_incident_id: "INC-014-B",
    raw_incident_ids: ["INC-014-A", "INC-014-B"],
    stream_name: "fusion",
    primary_frame_url: null,
    primary_thumbnail_url: null,
    per_modality_scores: {
      rgb: 0.88,
      thermal: 0.84,
    },
    thresholds: {
      alert: 0.75,
      hold: 0.55,
      aggregation_window_seconds: 5,
      drone_gap_seconds: 10,
    },
    gating_reason: "rgb+thermal",
    latency_ms: 86,
    evidence: {
      rgb: null,
      thermal: null,
    },
    media: {
      rgb: null,
      thermal: null,
    },
    objects: [],
    created_at: "2026-02-19T14:32:08Z",
    updated_at: "2026-02-19T14:32:11Z",
  });

  assert.equal(detail.id, "agg-014");
  assert.equal(detail.isAggregated, true);
  assert.equal(detail.startedAt, "2026-02-19T14:32:07Z");
  assert.equal(detail.lastSeenAt, "2026-02-19T14:32:11Z");
  assert.equal(detail.endedAt, "2026-02-19T14:32:11Z");
  assert.equal(detail.avgFusedConfidence, 0.9);
  assert.equal(detail.frameCount, 2);
  assert.equal(detail.droneFrameCount, 2);
  assert.equal(detail.representativeIncidentId, "INC-014-B");
  assert.deepEqual(detail.rawIncidentIds, ["INC-014-A", "INC-014-B"]);
  assert.deepEqual(detail.thresholds, [
    { key: "alert", label: "Alert", value: 0.75 },
    { key: "hold", label: "Hold", value: 0.55 },
  ]);
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
  assert.equal(detail.alertLevel, "Low");
  assert.equal(detail.gatingReason, "--");
  assert.equal(detail.visualScore, 0);
  assert.equal(detail.thermalScore, 0);
  assert.deepEqual(detail.rgbMedia, {
    frameUrl: null,
    thumbnailUrl: null,
  });
  assert.deepEqual(detail.thermalMedia, {
    frameUrl: null,
    thumbnailUrl: null,
  });
  assert.deepEqual(detail.thresholds, []);
  assert.deepEqual(detail.objects, []);
});
