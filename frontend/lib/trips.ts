import { apiConfig } from "@/lib/api";
import type { Coordinate, RouteCandidate } from "@/lib/navigation";

export type SafeTrip = {
  id: string;
  selected_route_id: string;
  origin: Coordinate;
  destination: Coordinate;
  distance_meters: number;
  estimated_duration_seconds: number;
  geometry: { coordinates: Coordinate[] };
  expected_arrival_at: string;
  status: "planned";
  created_at: string;
};

export class SafeTripApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "SafeTripApiError";
  }
}

export async function createSafeTrip(route: RouteCandidate, expectedArrivalAt: string): Promise<SafeTrip> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        selected_route_id: route.route_id,
        origin: route.origin,
        destination: route.destination,
        distance_meters: route.distance_meters,
        estimated_duration_seconds: route.estimated_duration_seconds,
        geometry: route.geometry,
        expected_arrival_at: new Date(expectedArrivalAt).toISOString(),
      }),
    });
  } catch {
    throw new SafeTripApiError("The Safe Trip service could not be reached.", 0);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new SafeTripApiError(body?.detail ?? "The Safe Trip could not be created.", response.status);
  }
  return (await response.json()) as SafeTrip;
}

