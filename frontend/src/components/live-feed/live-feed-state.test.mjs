import test from "node:test";
import assert from "node:assert/strict";
import {
  buildServiceItems,
  buildStreamPlaylistUrl,
  buildVideoSubLabel,
  toServiceStatus,
} from "./live-feed-state.mjs";

test("toServiceStatus maps backend stream states", () => {
  assert.equal(toServiceStatus("active"), "Connected");
  assert.equal(toServiceStatus("inactive"), "Disconnected");
  assert.equal(toServiceStatus("error"), "Unstable");
});

test("buildVideoSubLabel uses fallback when stream is missing", () => {
  assert.equal(buildVideoSubLabel(undefined, "1920x1080 • RGB"), "1920x1080 • RGB • Not available");
});

test("buildVideoSubLabel appends uppercase stream status", () => {
  assert.equal(
    buildVideoSubLabel({ status: "active" }, "640x480 • IR"),
    "640x480 • IR • ACTIVE",
  );
});

test("buildStreamPlaylistUrl builds API proxy url", () => {
  assert.equal(
    buildStreamPlaylistUrl("visual", "http://localhost:8000"),
    "http://localhost:8000/streams/visual/hls/index.m3u8",
  );
});

test("buildServiceItems falls back to disconnected when streams are unavailable", () => {
  const services = buildServiceItems(undefined, undefined, [{ name: "Backend", status: "Connected" }]);

  assert.deepEqual(services, [
    { name: "RGB Cam", status: "Disconnected" },
    { name: "Thermal Cam", status: "Disconnected" },
    { name: "Backend", status: "Connected" },
  ]);
});
