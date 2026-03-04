/**
 * @typedef {"Connected" | "Unstable" | "Disconnected"} ServiceStatus
 */

/**
 * @param {"active" | "inactive" | "error"} status
 * @returns {ServiceStatus}
 */
export function toServiceStatus(status) {
  if (status === "active") {
    return "Connected";
  }
  if (status === "inactive") {
    return "Disconnected";
  }
  return "Unstable";
}

/**
 * @param {{ status: "active" | "inactive" | "error" } | undefined} stream
 * @param {string} fallback
 * @returns {string}
 */
export function buildVideoSubLabel(stream, fallback) {
  if (!stream) {
    return `${fallback} • Not available`;
  }

  return `${fallback} • ${stream.status.toUpperCase()}`;
}

/**
 * @param {string} streamName
 * @param {string | undefined} [apiBaseUrl]
 * @returns {string}
 */
export function buildStreamPlaylistUrl(streamName, apiBaseUrl = undefined) {
  const baseUrl = (apiBaseUrl ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000")
    .replace(/\/+$/, "");
  const encodedStreamName = encodeURIComponent(streamName);
  return `${baseUrl}/streams/${encodedStreamName}/hls/index.m3u8`;
}

/**
 * @param {{ status: "active" | "inactive" | "error" } | undefined} visualStream
 * @param {{ status: "active" | "inactive" | "error" } | undefined} thermalStream
 * @param {{ name: string; status: ServiceStatus }[]} baseServices
 * @returns {{ name: string; status: ServiceStatus }[]}
 */
export function buildServiceItems(visualStream, thermalStream, baseServices) {
  return [
    { name: "RGB Cam", status: visualStream ? toServiceStatus(visualStream.status) : "Disconnected" },
    { name: "Thermal Cam", status: thermalStream ? toServiceStatus(thermalStream.status) : "Disconnected" },
    ...baseServices,
  ];
}
