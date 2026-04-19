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

export type GetIncidentsParams = {
  limit?: number;
  decision?: IncidentDecision;
  fromTs?: string;
  toTs?: string;
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

function buildApiUrl(path: string, searchParams?: URLSearchParams): string {
  const normalizedBase = getApiBaseUrl().endsWith("/")
    ? getApiBaseUrl()
    : `${getApiBaseUrl()}/`;
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const url = new URL(normalizedPath, normalizedBase);

  if (searchParams) {
    url.search = searchParams.toString();
  }

  return url.toString();
}

async function fetchApi<T>(path: string, searchParams?: URLSearchParams): Promise<T> {
  const response = await fetch(buildApiUrl(path, searchParams), {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    let errorDetail = "";

    try {
      const errorBody = await response.json();
      errorDetail =
        typeof errorBody?.detail === "string"
          ? errorBody.detail
          : JSON.stringify(errorBody?.detail ?? errorBody);
    } catch {
      try {
        errorDetail = await response.text();
      } catch {
        errorDetail = "";
      }
    }

    const message = errorDetail
      ? `Request failed (${response.status}): ${path} - ${errorDetail}`
      : `Request failed (${response.status}): ${path}`;

    console.error("Incidents API request failed", {
      path,
      status: response.status,
      url: buildApiUrl(path, searchParams),
      detail: errorDetail || null,
    });

    throw new Error(message);
  }

  return (await response.json()) as T;
}

export async function getIncidents(params: GetIncidentsParams = {}): Promise<IncidentResponse[]> {
  const searchParams = new URLSearchParams();

  if (typeof params.limit === "number") {
    searchParams.set("limit", String(params.limit));
  }

  if (params.decision) {
    searchParams.set("decision", params.decision);
  }

  if (params.fromTs) {
    searchParams.set("from_ts", params.fromTs);
  }

  if (params.toTs) {
    searchParams.set("to_ts", params.toTs);
  }

  return fetchApi<IncidentResponse[]>("/incidents", searchParams);
}
