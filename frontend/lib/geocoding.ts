import { apiConfig } from "@/lib/api";
import type { Coordinate } from "@/lib/navigation";

export type DestinationSuggestion = {
  suggestion_id: string;
  label: string;
  coordinate: Coordinate;
};

export type DestinationSearchResponse = {
  results: DestinationSuggestion[];
  count: number;
};

export class GeocodingApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "GeocodingApiError";
  }
}

function isSuggestion(value: unknown): value is DestinationSuggestion {
  if (!value || typeof value !== "object") return false;
  const suggestion = value as Partial<DestinationSuggestion>;
  const coordinate = suggestion.coordinate as Partial<Coordinate> | undefined;
  return (
    typeof suggestion.suggestion_id === "string" &&
    typeof suggestion.label === "string" &&
    typeof coordinate?.latitude === "number" &&
    typeof coordinate.longitude === "number"
  );
}

function parseResponse(value: unknown): DestinationSearchResponse {
  if (!value || typeof value !== "object") {
    throw new GeocodingApiError("The destination search response was invalid.", 200);
  }
  const response = value as Partial<DestinationSearchResponse>;
  if (
    typeof response.count !== "number" ||
    !Array.isArray(response.results) ||
    !response.results.every(isSuggestion)
  ) {
    throw new GeocodingApiError("The destination search response was invalid.", 200);
  }
  return response as DestinationSearchResponse;
}

export async function searchDestinations(query: string): Promise<DestinationSearchResponse> {
  const normalizedQuery = query.trim();
  if (normalizedQuery.length < 2) {
    throw new GeocodingApiError("Enter a destination to search.", 422);
  }
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/geocoding/search?q=${encodeURIComponent(normalizedQuery)}`);
  } catch {
    throw new GeocodingApiError("Destination search is temporarily unavailable.", 0);
  }
  if (!response.ok) {
    throw new GeocodingApiError(
      response.status === 429 || response.status >= 500
        ? "Destination search is temporarily unavailable."
        : "Destination search could not be completed.",
      response.status,
    );
  }
  return parseResponse(await response.json());
}
