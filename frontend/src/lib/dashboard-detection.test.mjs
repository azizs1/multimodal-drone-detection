import test from "node:test";
import assert from "node:assert/strict";
import {
  mapIncidentToDashboardRow,
  mapIncidentToDashboardSummary,
} from "./dashboard-detection.mjs";

const BASE_INCIDENT = {
  id: "row-1",
  incident_id: "incident-demo-011",
  detected_at: "2026-04-04T16:37:33.779219Z",
  source_timestamp: 1775320653.779219,
  has_drone: true,
  decision: "drone",
  confidence_band: "medium",
  alert_level: "medium",
  is_confirmed: true,
  fused_confidence: 0.72,
  stream_name: "fusion",
  primary_frame_url: null,
  primary_thumbnail_url: null,
  per_modality_scores: {
    rgb: 0.7,
    thermal: 0.58,
  },
  thresholds: {
    alert: 0.75,
    hold: 0.55,
  },
  gating_reason: "rgb+thermal",
  latency_ms: 0.02,
  evidence: {
    rgb: null,
    thermal: null,
  },
  media: {
    rgb: null,
    thermal: null,
  },
  objects: [],
  created_at: "2026-04-10T00:03:02.379642Z",
  updated_at: "2026-04-10T00:03:02.379642Z",
};

test("maps backend incidents into dashboard rows", () => {
  const mapped = mapIncidentToDashboardRow(BASE_INCIDENT);

  assert.equal(mapped.id, "incident-demo-011");
  assert.match(mapped.occurredAt, /^[A-Z][a-z]{2} \d{2}, \d{1,2}:\d{2} [AP]M$/);
  assert.equal(mapped.fusedConfidence, 72);
  assert.equal(mapped.visualConfidence, 70);
  assert.equal(mapped.thermalConfidence, 58);
  assert.equal(mapped.avgFusedConfidence, null);
  assert.equal(mapped.frameCount, null);
  assert.equal(mapped.lastSeenAt, null);
});

test("maps aggregated backend incidents into dashboard rows", () => {
  const mapped = mapIncidentToDashboardRow({
    ...BASE_INCIDENT,
    aggregate_id: "agg-demo-011",
    incident_id: "agg-demo-011",
    started_at: "2026-04-04T16:37:30.779219Z",
    last_seen_at: "2026-04-04T16:37:33.779219Z",
    frame_count: 2,
    drone_frame_count: 2,
    avg_fused_confidence: 0.7,
    representative_incident_id: "incident-demo-011",
    raw_incident_ids: ["incident-demo-010", "incident-demo-011"],
  });

  assert.equal(mapped.id, "agg-demo-011");
  assert.match(mapped.occurredAt, /^[A-Z][a-z]{2} \d{2}, \d{1,2}:\d{2} [AP]M$/);
  assert.equal(mapped.fusedConfidence, 72);
  assert.equal(mapped.visualConfidence, 70);
  assert.equal(mapped.thermalConfidence, 58);
  assert.equal(mapped.avgFusedConfidence, 70);
  assert.equal(mapped.frameCount, 2);
  assert.equal(mapped.lastSeenAt, "2026-04-04T16:37:33.779219Z");
});

test("derives dashboard summary metrics from latest incident", () => {
  assert.deepEqual(mapIncidentToDashboardSummary(BASE_INCIDENT), {
    fusedConfidence: 72,
    visualConfidence: 70,
    thermalConfidence: 58,
  });
});

test("falls back to zero when per-modality scores are missing", () => {
  assert.deepEqual(
    mapIncidentToDashboardSummary({
      ...BASE_INCIDENT,
      per_modality_scores: {},
    }),
    {
      fusedConfidence: 72,
      visualConfidence: 0,
      thermalConfidence: 0,
    },
  );
});

test("returns an empty summary when no incident is available", () => {
  assert.deepEqual(mapIncidentToDashboardSummary(undefined), {
    fusedConfidence: 0,
    visualConfidence: 0,
    thermalConfidence: 0,
  });
});
