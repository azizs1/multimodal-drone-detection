export type StreamStatus = "active" | "inactive" | "error";

export type StreamInfo = {
  name: string;
  description: string;
  rtsp_url: string;
  hls_url: string;
  status: StreamStatus;
};

export type StreamListResponse = {
  streams: StreamInfo[];
  total: number;
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed (${response.status}): ${path}`);
  }

  return (await response.json()) as T;
}

export async function getStreams(): Promise<StreamListResponse> {
  return fetchApi<StreamListResponse>("/streams");
}

export async function getStreamByName(streamName: string): Promise<StreamInfo> {
  return fetchApi<StreamInfo>(`/streams/${streamName}`);
}
