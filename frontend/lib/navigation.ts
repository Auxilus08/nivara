import { apiConfig } from "@/lib/api";

export type RouteMode = "fastest" | "balanced" | "safety_priority";

export type Coordinate = {
  latitude: number;
  longitude: number;
};

export type RouteCandidate = {
  route_id: string;
  origin: Coordinate;
  destination: Coordinate;
  distance_meters: number;
  estimated_duration_seconds: number;
  geometry: { coordinates: Coordinate[] } | null;
  provider: string;
  provider_metadata: Record<string, string>;
  safety_assessment: {
    risk_score: number;
    risk_level: string;
    confidence: string;
    factors: { name: string; contribution: number; description: string }[];
    disclaimer: string;
  } | null;
  normalized_travel_score: number | null;
  comparison_cost: number | null;
  comparison_explanation: string | null;
};

export type RouteResponse = {
  mode: RouteMode;
  routes: RouteCandidate[];
  selected_route_id: string | null;
  comparison_explanation: string;
};

export type HeatmapViewport = {
  min_latitude: number;
  min_longitude: number;
  max_latitude: number;
  max_longitude: number;
};

export type HeatmapPoint = {
  latitude: number;
  longitude: number;
  risk_score: number;
  risk_level: "low" | "moderate" | "elevated" | "high";
  incident_count: number;
  confidence: "low" | "medium" | "high";
};

export type HeatmapResponse = {
  bounds: HeatmapViewport;
  rows: number;
  columns: number;
  points: HeatmapPoint[];
  incident_count: number;
  disclaimer: string;
};

export class NavigationApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "NavigationApiError";
  }
}

export async function calculateRoutes(
  origin: Coordinate,
  destination: Coordinate,
  mode: RouteMode,
): Promise<RouteResponse> {
  let response: Response | undefined;
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      response = await fetch(`${apiConfig.baseUrl}/routes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origin, destination, mode }),
      });
    } catch {
      throw new NavigationApiError("The navigation service could not be reached.", 0);
    }

    if (response.ok || response.status < 500 || attempt === 1) {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }

  if (!response) {
    throw new NavigationApiError("The navigation service could not be reached.", 0);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: { message?: string } }
      | null;
    throw new NavigationApiError(
      body?.detail?.message ?? "The navigation provider is currently unavailable.",
      response.status,
    );
  }

  return (await response.json()) as RouteResponse;
}

function isHeatmapResponse(value: unknown): value is HeatmapResponse {
  if (!value || typeof value !== "object") return false;
  const response = value as Partial<HeatmapResponse>;
  const bounds = response.bounds as Partial<HeatmapViewport> | undefined;
  const points = response.points;
  return (
    typeof response.rows === "number" &&
    typeof response.columns === "number" &&
    typeof response.incident_count === "number" &&
    typeof response.disclaimer === "string" &&
    typeof bounds?.min_latitude === "number" &&
    typeof bounds.min_longitude === "number" &&
    typeof bounds.max_latitude === "number" &&
    typeof bounds.max_longitude === "number" &&
    Array.isArray(points) &&
    points.every((point) => {
      if (!point || typeof point !== "object") return false;
      const candidate = point as Partial<HeatmapPoint>;
      return (
        typeof candidate.latitude === "number" &&
        typeof candidate.longitude === "number" &&
        typeof candidate.risk_score === "number" &&
        typeof candidate.risk_level === "string" &&
        typeof candidate.incident_count === "number" &&
        typeof candidate.confidence === "string"
      );
    })
  );
}

export async function calculateHeatmap(viewport: HeatmapViewport): Promise<HeatmapResponse> {
  const params = new URLSearchParams({
    min_latitude: String(viewport.min_latitude),
    min_longitude: String(viewport.min_longitude),
    max_latitude: String(viewport.max_latitude),
    max_longitude: String(viewport.max_longitude),
    rows: "8",
    columns: "8",
  });
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/safety/heatmap?${params.toString()}`);
  } catch {
    throw new NavigationApiError("The safety indicators could not be reached.", 0);
  }

  if (!response.ok) {
    throw new NavigationApiError(
      "The contextual safety indicators are currently unavailable.",
      response.status,
    );
  }

  const body: unknown = await response.json();
  if (!isHeatmapResponse(body)) {
    throw new NavigationApiError("The safety indicator response was invalid.", response.status);
  }
  return body;
}
