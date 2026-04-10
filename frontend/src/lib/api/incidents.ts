export type IncidentDecision = "drone" | "none";
export type IncidentConfidenceBand = "low" | "medium" | "high";

export type IncidentResponse = {
  id: string;
  incident_id: string;
  detected_at: string;
  source_timestamp: number;
  has_drone: boolean;
  decision: IncidentDecision;
  confidence_band: IncidentConfidenceBand;
  alert_level: IncidentConfidenceBand;
  is_confirmed: boolean;
  fused_confidence: number;
  stream_name: string;
  primary_frame_url: string | null;
  primary_thumbnail_url: string | null;
  per_modality_scores: {
    rgb?: number;
    thermal?: number;
  };
  thresholds: Record<string, number>;
  gating_reason: string;
  latency_ms: number;
  evidence: Record<string, unknown>;
  media: Record<string, unknown>;
  objects: unknown[];
  created_at: string;
  updated_at: string;
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

function buildApiUrl(path: string): string {
  const normalizedBase = getApiBaseUrl().endsWith("/")
    ? getApiBaseUrl()
    : `${getApiBaseUrl()}/`;
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  return new URL(normalizedPath, normalizedBase).toString();
}

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed (${response.status}): ${path}`);
  }

  return (await response.json()) as T;
}

export async function getIncidents(): Promise<IncidentResponse[]> {
  return fetchApi<IncidentResponse[]>("/incidents");
}
