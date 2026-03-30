import test from "node:test";
import assert from "node:assert/strict";
import { MOCK_DASHBOARD_INCIDENT_ROWS } from "./dashboard-detection.mjs";

test("mock dashboard incidents expose fused confidence and distance fields", () => {
  assert.equal(MOCK_DASHBOARD_INCIDENT_ROWS.length, 5);
  assert.deepEqual(MOCK_DASHBOARD_INCIDENT_ROWS[0], {
    id: "#001",
    occurredAt: "14:32:07",
    fusedConfidence: 94,
    distanceFt: 14,
    status: "Confirmed",
  });
});

test("mock dashboard incidents keep a stable frontend view model shape", () => {
  for (const incident of MOCK_DASHBOARD_INCIDENT_ROWS) {
    assert.equal(typeof incident.id, "string");
    assert.equal(typeof incident.occurredAt, "string");
    assert.equal(typeof incident.fusedConfidence, "number");
    assert.equal(typeof incident.distanceFt, "number");
    assert.ok(["Confirmed", "Pending", "False Positive"].includes(incident.status));
  }
});
