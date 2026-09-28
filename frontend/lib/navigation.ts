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
    disclaimer: string;
  } | null;
};

export type RouteResponse = {
  mode: RouteMode;
  routes: RouteCandidate[];
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
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/routes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ origin, destination, mode }),
    });
  } catch {
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
