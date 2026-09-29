import { apiConfig } from "./api";
import type { Coordinate } from "./navigation";

export type SafePlaceCategory = "hospital" | "police_station" | "petrol_pump" | "hotel" | "open_business";
export type SafePlace = { id: string; name: string; category: SafePlaceCategory; latitude: number; longitude: number; distance_meters: number; is_demo_resource: boolean };

export async function getNearbySafePlaces(location: Coordinate, radius = 5000, category?: SafePlaceCategory): Promise<{ resources: SafePlace[]; count: number; disclaimer: string }> {
  const params = new URLSearchParams({ latitude: String(location.latitude), longitude: String(location.longitude), radius: String(radius) });
  if (category) params.set("category", category);
  const response = await fetch(`${apiConfig.baseUrl}/safe-places/nearby?${params}`);
  if (!response.ok) throw new Error("Nearby assistance resources are unavailable.");
  const body = await response.json() as { resources?: unknown; count?: unknown; disclaimer?: unknown };
  if (!Array.isArray(body.resources) || typeof body.count !== "number" || typeof body.disclaimer !== "string") throw new Error("The assistance resource response was invalid.");
  return body as { resources: SafePlace[]; count: number; disclaimer: string };
}

export type PrivacySettings = { location_sharing_enabled: boolean; trusted_contact_sharing_enabled: boolean; emergency_sharing_enabled: boolean; prototype_scope: string };
export async function getPrivacySettings(): Promise<PrivacySettings> {
  const response = await fetch(`${apiConfig.baseUrl}/privacy/settings`);
  if (!response.ok) throw new Error("Privacy settings are unavailable.");
  return response.json() as Promise<PrivacySettings>;
}
export async function updatePrivacySettings(changes: Partial<Pick<PrivacySettings, "location_sharing_enabled" | "trusted_contact_sharing_enabled" | "emergency_sharing_enabled">>): Promise<PrivacySettings> {
  const response = await fetch(`${apiConfig.baseUrl}/privacy/settings`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes) });
  if (!response.ok) throw new Error("Privacy settings could not be updated.");
  return response.json() as Promise<PrivacySettings>;
}
