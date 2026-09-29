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
  status: "planned" | "active" | "completed";
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type SafeTripLocation = {
  id: string;
  trip_id: string;
  latitude: number;
  longitude: number;
  recorded_at: string;
  received_at: string;
};

export type SafeTripDeviationAssessment = {
  trip_id: string;
  deviated: boolean;
  distance_from_route_meters: number;
  threshold_meters: number;
  based_on_location_id: string;
  evaluated_at: string;
  explanation: string;
};

export type SafeTripCheckIn = {
  id: string;
  trip_id: string;
  checked_in_at: string;
};

export type SafeTripHistoryItem = {
  id: string;
  status: "planned" | "active" | "completed";
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  expected_arrival_at: string;
  origin: Coordinate;
  destination: Coordinate;
};

export type SafeTripHistoryResponse = {
  trips: SafeTripHistoryItem[];
  count: number;
};

export type TrustedContact = {
  id: string;
  name: string;
  contact_method: "phone" | "email";
  contact_value: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TrustedContactListResponse = {
  contacts: TrustedContact[];
  count: number;
};

export type TrustedContactSharingPreferences = {
  trusted_contact_id: string;
  allow_trip_status: boolean;
  allow_location: boolean;
  allow_emergency: boolean;
  created_at: string;
  updated_at: string;
};

export type SafeTripTrustedContact = {
  safe_trip_id: string;
  trusted_contact_id: string;
  created_at: string;
  contact: TrustedContact;
};

export type SafeTripTrustedContactListResponse = {
  contacts: SafeTripTrustedContact[];
  count: number;
};

export type Emergency = {
  id: string;
  trip_id: string | null;
  status: "active" | "acknowledged" | "resolved";
  emergency_type: string;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  notification_mode: "mock_demo_only";
  sharing_status: "sharing_disabled" | "demo_notification_only";
};

export type EmergencyResource = {
  id: string;
  category: string;
  name: string;
  description: string;
  is_demo_resource: boolean;
};

export type EmergencyResourceListResponse = {
  resources: EmergencyResource[];
  count: number;
  disclaimer: string;
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

export async function startSafeTrip(tripId: string): Promise<SafeTrip> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/start`, { method: "POST" });
  } catch {
    throw new SafeTripApiError("The Safe Trip service could not be reached.", 0);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new SafeTripApiError(body?.detail ?? "The Safe Trip could not be started.", response.status);
  }
  return (await response.json()) as SafeTrip;
}

export async function completeSafeTrip(tripId: string): Promise<SafeTrip> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/complete`, { method: "POST" });
  } catch {
    throw new SafeTripApiError("Could not complete the Safe Trip.", 0);
  }

  if (!response.ok) {
    if (response.status === 404) {
      throw new SafeTripApiError("This Safe Trip could not be found.", response.status);
    }
    if (response.status === 409) {
      throw new SafeTripApiError("Only an active Safe Trip can be completed.", response.status);
    }
    throw new SafeTripApiError("Could not complete the Safe Trip.", response.status);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!payload || typeof payload !== "object") {
    throw new SafeTripApiError("The completion response was invalid.", response.status);
  }
  const trip = payload as Partial<SafeTrip>;
  if (typeof trip.id !== "string" || trip.status !== "completed" || typeof trip.completed_at !== "string") {
    throw new SafeTripApiError("The completion response was invalid.", response.status);
  }
  return payload as SafeTrip;
}

function isSafeTripHistoryItem(value: unknown): value is SafeTripHistoryItem {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  const origin = item.origin as Record<string, unknown> | undefined;
  const destination = item.destination as Record<string, unknown> | undefined;
  return (
    typeof item.id === "string" &&
    (item.status === "planned" || item.status === "active" || item.status === "completed") &&
    typeof item.created_at === "string" &&
    (item.started_at === null || typeof item.started_at === "string") &&
    (item.completed_at === null || typeof item.completed_at === "string") &&
    typeof item.expected_arrival_at === "string" &&
    typeof origin?.latitude === "number" &&
    typeof origin.longitude === "number" &&
    typeof destination?.latitude === "number" &&
    typeof destination.longitude === "number"
  );
}

export async function getSafeTripHistory(): Promise<SafeTripHistoryResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/history`);
  } catch {
    throw new SafeTripApiError("Could not load Safe Trip history.", 0);
  }

  if (!response.ok) {
    throw new SafeTripApiError("Could not load Safe Trip history.", response.status);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!payload || typeof payload !== "object") {
    throw new SafeTripApiError("The Safe Trip history response was invalid.", response.status);
  }
  const history = payload as { trips?: unknown; count?: unknown };
  if (!Array.isArray(history.trips) || typeof history.count !== "number" || !history.trips.every(isSafeTripHistoryItem)) {
    throw new SafeTripApiError("The Safe Trip history response was invalid.", response.status);
  }
  return { trips: history.trips, count: history.count };
}

function isTrustedContact(value: unknown): value is TrustedContact {
  if (!value || typeof value !== "object") return false;
  const contact = value as Record<string, unknown>;
  return (
    typeof contact.id === "string" &&
    typeof contact.name === "string" &&
    (contact.contact_method === "phone" || contact.contact_method === "email") &&
    typeof contact.contact_value === "string" &&
    typeof contact.is_active === "boolean" &&
    typeof contact.created_at === "string" &&
    typeof contact.updated_at === "string"
  );
}

export async function getTrustedContacts(): Promise<TrustedContactListResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trusted-contacts`);
  } catch {
    throw new SafeTripApiError("Could not load trusted contacts.", 0);
  }
  if (!response.ok) throw new SafeTripApiError("Could not load trusted contacts.", response.status);

  const payload: unknown = await response.json().catch(() => null);
  if (!payload || typeof payload !== "object") {
    throw new SafeTripApiError("The trusted contacts response was invalid.", response.status);
  }
  const list = payload as { contacts?: unknown; count?: unknown };
  if (!Array.isArray(list.contacts) || typeof list.count !== "number" || !list.contacts.every(isTrustedContact)) {
    throw new SafeTripApiError("The trusted contacts response was invalid.", response.status);
  }
  return { contacts: list.contacts, count: list.count };
}

export async function createTrustedContact(
  name: string,
  contactMethod: TrustedContact["contact_method"],
  contactValue: string,
): Promise<TrustedContact> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trusted-contacts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, contact_method: contactMethod, contact_value: contactValue }),
    });
  } catch {
    throw new SafeTripApiError("Could not add trusted contact.", 0);
  }
  if (!response.ok) {
    throw new SafeTripApiError(
      response.status === 422 ? "Enter a valid name and contact value." : "Could not add trusted contact.",
      response.status,
    );
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isTrustedContact(payload)) {
    throw new SafeTripApiError("The trusted contact response was invalid.", response.status);
  }
  return payload;
}

export async function updateTrustedContact(
  contactId: string,
  changes: Partial<Pick<TrustedContact, "name" | "contact_method" | "contact_value">>,
): Promise<TrustedContact> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trusted-contacts/${contactId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(changes),
    });
  } catch {
    throw new SafeTripApiError("Could not update trusted contact.", 0);
  }
  if (!response.ok) {
    if (response.status === 404) throw new SafeTripApiError("Trusted contact was not found.", response.status);
    if (response.status === 422) throw new SafeTripApiError("Enter a valid name and contact value.", response.status);
    throw new SafeTripApiError("Could not update trusted contact.", response.status);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isTrustedContact(payload)) {
    throw new SafeTripApiError("The trusted contact response was invalid.", response.status);
  }
  return payload;
}

export async function deleteTrustedContact(contactId: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trusted-contacts/${contactId}`, { method: "DELETE" });
  } catch {
    throw new SafeTripApiError("Could not remove trusted contact.", 0);
  }
  if (!response.ok) {
    throw new SafeTripApiError(
      response.status === 404 ? "Trusted contact was not found." : "Could not remove trusted contact.",
      response.status,
    );
  }
}

function isTrustedContactSharingPreferences(value: unknown): value is TrustedContactSharingPreferences {
  if (!value || typeof value !== "object") return false;
  const preferences = value as Record<string, unknown>;
  return (
    typeof preferences.trusted_contact_id === "string" &&
    typeof preferences.allow_trip_status === "boolean" &&
    typeof preferences.allow_location === "boolean" &&
    typeof preferences.allow_emergency === "boolean" &&
    typeof preferences.created_at === "string" &&
    typeof preferences.updated_at === "string"
  );
}

export async function getTrustedContactSharingPreferences(
  contactId: string,
): Promise<TrustedContactSharingPreferences> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trusted-contacts/${contactId}/sharing-preferences`);
  } catch {
    throw new SafeTripApiError("Could not load sharing preferences.", 0);
  }
  if (!response.ok) {
    if (response.status === 404) throw new SafeTripApiError("Trusted contact was not found.", response.status);
    throw new SafeTripApiError("Could not load sharing preferences.", response.status);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isTrustedContactSharingPreferences(payload)) {
    throw new SafeTripApiError("The sharing-preference response was invalid.", response.status);
  }
  return payload;
}

export async function updateTrustedContactSharingPreferences(
  contactId: string,
  changes: Partial<Pick<TrustedContactSharingPreferences, "allow_trip_status" | "allow_location" | "allow_emergency">>,
): Promise<TrustedContactSharingPreferences> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trusted-contacts/${contactId}/sharing-preferences`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(changes),
    });
  } catch {
    throw new SafeTripApiError("Could not update sharing preferences.", 0);
  }
  if (!response.ok) {
    if (response.status === 404) throw new SafeTripApiError("Trusted contact was not found.", response.status);
    if (response.status === 422) throw new SafeTripApiError("Select at least one sharing preference.", response.status);
    throw new SafeTripApiError("Could not update sharing preferences.", response.status);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isTrustedContactSharingPreferences(payload)) {
    throw new SafeTripApiError("The sharing-preference response was invalid.", response.status);
  }
  return payload;
}

function isSafeTripTrustedContact(value: unknown): value is SafeTripTrustedContact {
  if (!value || typeof value !== "object") return false;
  const association = value as Record<string, unknown>;
  return (
    typeof association.safe_trip_id === "string" &&
    typeof association.trusted_contact_id === "string" &&
    typeof association.created_at === "string" &&
    isTrustedContact(association.contact)
  );
}

export async function getSafeTripTrustedContacts(tripId: string): Promise<SafeTripTrustedContactListResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/trusted-contacts`);
  } catch {
    throw new SafeTripApiError("Could not load trusted contacts for this Safe Trip.", 0);
  }
  if (!response.ok) {
    throw new SafeTripApiError(
      response.status === 404 ? "This Safe Trip could not be found." : "Could not load trusted contacts for this Safe Trip.",
      response.status,
    );
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!payload || typeof payload !== "object") {
    throw new SafeTripApiError("The Safe Trip contact response was invalid.", response.status);
  }
  const list = payload as { contacts?: unknown; count?: unknown };
  if (!Array.isArray(list.contacts) || typeof list.count !== "number" || !list.contacts.every(isSafeTripTrustedContact)) {
    throw new SafeTripApiError("The Safe Trip contact response was invalid.", response.status);
  }
  return { contacts: list.contacts, count: list.count };
}

export async function attachSafeTripTrustedContact(
  tripId: string,
  trustedContactId: string,
): Promise<SafeTripTrustedContact> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/trusted-contacts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trusted_contact_id: trustedContactId }),
    });
  } catch {
    throw new SafeTripApiError("Could not select the trusted contact for this Safe Trip.", 0);
  }
  if (!response.ok) {
    if (response.status === 404) throw new SafeTripApiError("The Safe Trip or trusted contact was not found.", response.status);
    if (response.status === 409) throw new SafeTripApiError("That trusted contact is already selected or the trip cannot be modified.", response.status);
    throw new SafeTripApiError("Could not select the trusted contact for this Safe Trip.", response.status);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isSafeTripTrustedContact(payload)) {
    throw new SafeTripApiError("The Safe Trip contact response was invalid.", response.status);
  }
  return payload;
}

export async function removeSafeTripTrustedContact(tripId: string, trustedContactId: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/trusted-contacts/${trustedContactId}`, {
      method: "DELETE",
    });
  } catch {
    throw new SafeTripApiError("Could not remove the trusted contact from this Safe Trip.", 0);
  }
  if (!response.ok) {
    if (response.status === 404) throw new SafeTripApiError("The trusted contact selection was not found.", response.status);
    if (response.status === 409) throw new SafeTripApiError("Completed Safe Trips cannot be modified.", response.status);
    throw new SafeTripApiError("Could not remove the trusted contact from this Safe Trip.", response.status);
  }
}

export async function recordSafeTripLocation(
  tripId: string,
  latitude: number,
  longitude: number,
  recordedAt: string,
): Promise<SafeTripLocation> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/locations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latitude, longitude, recorded_at: recordedAt }),
    });
  } catch {
    throw new SafeTripApiError("The Safe Trip service could not be reached.", 0);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new SafeTripApiError(body?.detail ?? "The location update could not be recorded.", response.status);
  }
  return (await response.json()) as SafeTripLocation;
}

function isSafeTripDeviationAssessment(value: unknown): value is SafeTripDeviationAssessment {
  if (!value || typeof value !== "object") return false;
  const assessment = value as Record<string, unknown>;
  return (
    typeof assessment.trip_id === "string" &&
    typeof assessment.deviated === "boolean" &&
    typeof assessment.distance_from_route_meters === "number" &&
    typeof assessment.threshold_meters === "number" &&
    typeof assessment.based_on_location_id === "string" &&
    typeof assessment.evaluated_at === "string" &&
    typeof assessment.explanation === "string"
  );
}

export async function getSafeTripDeviation(tripId: string): Promise<SafeTripDeviationAssessment> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/deviation`);
  } catch {
    throw new SafeTripApiError("Could not check route status.", 0);
  }

  if (!response.ok) {
    if (response.status === 404) {
      throw new SafeTripApiError("This Safe Trip could not be found.", response.status);
    }
    if (response.status === 409) {
      throw new SafeTripApiError(
        "Route status is unavailable until a location is recorded while the Safe Trip is active.",
        response.status,
      );
    }
    throw new SafeTripApiError("Could not check route status.", response.status);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!isSafeTripDeviationAssessment(payload)) {
    throw new SafeTripApiError("The route status response was invalid.", response.status);
  }
  return payload;
}

function isEmergency(value: unknown): value is Emergency {
  if (!value || typeof value !== "object") return false;
  const item = value as Record<string, unknown>;
  return typeof item.id === "string" && (item.trip_id === null || typeof item.trip_id === "string") &&
    (item.status === "active" || item.status === "acknowledged" || item.status === "resolved") &&
    typeof item.emergency_type === "string" && typeof item.created_at === "string" &&
    (item.latitude === null || typeof item.latitude === "number") &&
    (item.longitude === null || typeof item.longitude === "number") &&
    (item.acknowledged_at === null || typeof item.acknowledged_at === "string") &&
    (item.resolved_at === null || typeof item.resolved_at === "string") && item.notification_mode === "mock_demo_only" &&
    (item.sharing_status === "sharing_disabled" || item.sharing_status === "demo_notification_only");
}

async function emergencyRequest(path: string, method: "POST" = "POST", message: string): Promise<Emergency> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}${path}`, { method });
  } catch {
    throw new SafeTripApiError("The emergency service could not be reached.", 0);
  }
  if (!response.ok) {
    if (response.status === 404) throw new SafeTripApiError("The emergency or Safe Trip was not found.", response.status);
    if (response.status === 409) throw new SafeTripApiError("This emergency action is not valid for the current state.", response.status);
    throw new SafeTripApiError(message, response.status);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isEmergency(payload)) throw new SafeTripApiError("The emergency response was invalid.", response.status);
  return payload;
}

export async function createEmergency(tripId?: string): Promise<Emergency> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/emergencies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(tripId ? { trip_id: tripId, emergency_type: "sos" } : { emergency_type: "sos" }),
    });
  } catch {
    throw new SafeTripApiError("The emergency service could not be reached.", 0);
  }
  if (!response.ok) {
    if (response.status === 404) throw new SafeTripApiError("The Safe Trip was not found.", response.status);
    if (response.status === 409) throw new SafeTripApiError("An active emergency already exists or the trip is not active.", response.status);
    throw new SafeTripApiError("Could not activate the demo emergency workflow.", response.status);
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!isEmergency(payload)) throw new SafeTripApiError("The emergency response was invalid.", response.status);
  return payload;
}

export function acknowledgeEmergency(emergencyId: string): Promise<Emergency> {
  return emergencyRequest(`/emergencies/${emergencyId}/acknowledge`, "POST", "Could not acknowledge the emergency.");
}

export function resolveEmergency(emergencyId: string): Promise<Emergency> {
  return emergencyRequest(`/emergencies/${emergencyId}/resolve`, "POST", "Could not resolve the emergency.");
}

export async function getEmergencyResources(): Promise<EmergencyResourceListResponse> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/emergencies/resources`);
  } catch {
    throw new SafeTripApiError("Could not load emergency resources.", 0);
  }
  if (!response.ok) throw new SafeTripApiError("Could not load emergency resources.", response.status);
  const payload = await response.json().catch(() => null) as Partial<EmergencyResourceListResponse> | null;
  if (!payload || !Array.isArray(payload.resources) || typeof payload.count !== "number" || typeof payload.disclaimer !== "string") {
    throw new SafeTripApiError("The emergency resources response was invalid.", response.status);
  }
  return payload as EmergencyResourceListResponse;
}

function isSafeTripCheckIn(value: unknown): value is SafeTripCheckIn {
  if (!value || typeof value !== "object") return false;
  const checkIn = value as Record<string, unknown>;
  return (
    typeof checkIn.id === "string" &&
    typeof checkIn.trip_id === "string" &&
    typeof checkIn.checked_in_at === "string"
  );
}

export async function recordSafeTripCheckIn(tripId: string): Promise<SafeTripCheckIn> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}/trips/${tripId}/check-ins`, { method: "POST" });
  } catch {
    throw new SafeTripApiError("Could not record the journey check-in.", 0);
  }

  if (!response.ok) {
    if (response.status === 404) {
      throw new SafeTripApiError("This Safe Trip could not be found.", response.status);
    }
    if (response.status === 409) {
      throw new SafeTripApiError("Check-in is available only while the Safe Trip is active.", response.status);
    }
    throw new SafeTripApiError("Could not record the journey check-in.", response.status);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!isSafeTripCheckIn(payload)) {
    throw new SafeTripApiError("The check-in response was invalid.", response.status);
  }
  return payload;
}
