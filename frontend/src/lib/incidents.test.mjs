import test from "node:test";
import assert from "node:assert/strict";
import { mapIncidentRowToDetail } from "./incidents.mjs";

test("mapIncidentRowToDetail maps confirmed incidents to a drone decision", () => {
  const detail = mapIncidentRowToDetail({
    id: "#014",
    timestamp: "2026-02-19T14:32:07",
    confidence: 94,
    distanceFt: 12,
    model: "HolyStone-v2",
    status: "Confirmed",
  });

  assert.deepEqual(detail, {
    id: "#014",
    timestamp: "2026-02-19T14:32:07",
    fusedConfidence: 94,
    confidenceBand: "High",
    decision: "Drone",
    status: "Confirmed",
    gatingReason: "Fusion threshold exceeded across available modalities.",
    latencyMs: 86,
    visualScore: 92,
    thermalScore: 89,
    rgbMediaLabel: "RGB snapshot reference for #014",
    thermalMediaLabel: "Thermal snapshot reference for #014",
    thresholdLabel: "Confidence threshold and gating rules will be surfaced from the fused payload.",
    objectsLabel: "Detected object summaries and overlay metadata will be rendered here.",
  });
});

test("mapIncidentRowToDetail maps false positives to no-drone detail state", () => {
  const detail = mapIncidentRowToDetail({
    id: "#015",
    timestamp: "2026-02-19T14:36:11",
    confidence: 72,
    distanceFt: 14,
    model: "HolyStone",
    status: "False Positive",
  });

  assert.equal(detail.decision, "No Drone");
  assert.equal(detail.confidenceBand, "Low");
  assert.equal(detail.gatingReason, "Confidence did not hold after analyst review.");
});
