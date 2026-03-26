import test from "node:test";
import assert from "node:assert/strict";
import {
  mapRealtimeAlertSeverity,
  mapRealtimeAlertToBannerData,
} from "./alerts.ts";

test("mapRealtimeAlertSeverity maps high confidence to critical", () => {
  assert.equal(mapRealtimeAlertSeverity("high"), "critical");
});

test("mapRealtimeAlertSeverity maps medium confidence to warning", () => {
  assert.equal(mapRealtimeAlertSeverity("medium"), "warning");
});

test("mapRealtimeAlertSeverity maps low confidence to info", () => {
  assert.equal(mapRealtimeAlertSeverity("low"), "info");
});

test("mapRealtimeAlertToBannerData returns null when decision is not drone", () => {
  const alert = mapRealtimeAlertToBannerData({
    incidentId: "evt-001",
    decision: "none",
    fusedConfidence: 0.91,
    confidenceBand: "high",
    gatingReason: "rgb+thermal threshold",
    timestamp: 1_743_020_736,
    streamName: "visual",
  });

  assert.equal(alert, null);
});

test("mapRealtimeAlertToBannerData builds critical banner data for drone detections", () => {
  const alert = mapRealtimeAlertToBannerData({
    incidentId: "evt-002",
    decision: "drone",
    fusedConfidence: 0.91,
    confidenceBand: "high",
    gatingReason: "rgb+thermal threshold",
    timestamp: 1_743_020_736,
    streamName: "visual",
  });

  assert.deepEqual(alert, {
    id: "evt-002",
    title: "Drone detected",
    message: "Fusion confidence exceeded alert threshold (rgb+thermal threshold).",
    severity: "critical",
    source: "fusion",
    occurredAt: new Date(1_743_020_736 * 1000).toISOString(),
    confidence: 0.91,
    confidenceBand: "high",
    streamName: "visual",
    dismissible: true,
  });
});

test("mapRealtimeAlertToBannerData uses generic messaging when threshold is not mentioned", () => {
  const alert = mapRealtimeAlertToBannerData({
    incidentId: "evt-003",
    decision: "drone",
    fusedConfidence: 0.86,
    confidenceBand: "high",
    gatingReason: "thermal confirmation",
    timestamp: 1_743_020_736,
    streamName: "thermal",
  });

  assert.equal(
    alert?.message,
    "Fusion decision flagged a drone event (thermal confirmation).",
  );
});
