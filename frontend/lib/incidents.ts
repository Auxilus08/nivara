import { apiConfig } from "@/lib/api";

export const incidentCategories = [
  "harassment",
  "theft",
  "suspicious_activity",
  "poor_lighting",
  "unsafe_isolated_area",
  "other",
] as const;

export const incidentSeverities = ["low", "medium", "high"] as const;
export const incidentStatuses = ["unverified", "corroborated", "validated", "rejected"] as const;
export const incidentConfidenceLevels = ["unverified", "corroborated", "higher_confidence"] as const;

export type IncidentCategory = (typeof incidentCategories)[number];
export type IncidentSeverity = (typeof incidentSeverities)[number];
export type IncidentStatus = (typeof incidentStatuses)[number];
export type IncidentConfidenceLevel = (typeof incidentConfidenceLevels)[number];

export type Incident = {
  id: string;
  category: IncidentCategory;
  description: string;
  latitude: number;
  longitude: number;
  occurred_at: string;
  reported_at: string;
  severity: IncidentSeverity;
  source: string;
  status: IncidentStatus;
  confidence: {
    level: IncidentConfidenceLevel;
    corroboration_count: number;
    factors: string[];
  };
  created_at: string;
  updated_at: string;
};

export type IncidentListFilters = {
  category?: IncidentCategory;
  severity?: IncidentSeverity;
  status?: IncidentStatus;
  confidence_level?: IncidentConfidenceLevel;
  occurred_from?: string;
  occurred_to?: string;
  latitude?: number;
  longitude?: number;
  radius_meters?: number;
};

export type IncidentListResponse = {
  items: Incident[];
  limit: number;
  count: number;
};

export type IncidentReport = {
  category: IncidentCategory;
  description: string;
  latitude: number;
  longitude: number;
  occurred_at?: string;
  severity: IncidentSeverity;
};

export class IncidentApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = "IncidentApiError";
  }
}

function isOneOf<T extends readonly string[]>(value: unknown, values: T): value is T[number] {
  return typeof value === "string" && values.includes(value);
}

function isIncident(value: unknown): value is Incident {
  if (!value || typeof value !== "object") return false;
  const incident = value as Partial<Incident>;
  const confidence = incident.confidence as Partial<Incident["confidence"]> | undefined;
  return (
    typeof incident.id === "string" &&
    isOneOf(incident.category, incidentCategories) &&
    typeof incident.description === "string" &&
    typeof incident.latitude === "number" &&
    typeof incident.longitude === "number" &&
    typeof incident.occurred_at === "string" &&
    typeof incident.reported_at === "string" &&
    isOneOf(incident.severity, incidentSeverities) &&
    typeof incident.source === "string" &&
    isOneOf(incident.status, incidentStatuses) &&
    typeof confidence?.corroboration_count === "number" &&
    isOneOf(confidence.level, incidentConfidenceLevels) &&
    Array.isArray(confidence.factors) &&
    confidence.factors.every((factor) => typeof factor === "string") &&
    typeof incident.created_at === "string" &&
    typeof incident.updated_at === "string"
  );
}

function parseIncident(value: unknown): Incident {
  if (!isIncident(value)) throw new IncidentApiError("The incident response was invalid.", 200);
  return value;
}

function parseIncidentList(value: unknown): IncidentListResponse {
  if (!value || typeof value !== "object") {
    throw new IncidentApiError("The incident list response was invalid.", 200);
  }
  const response = value as Partial<IncidentListResponse>;
  if (
    typeof response.limit !== "number" ||
    typeof response.count !== "number" ||
    !Array.isArray(response.items) ||
    !response.items.every(isIncident)
  ) {
    throw new IncidentApiError("The incident list response was invalid.", 200);
  }
  return response as IncidentListResponse;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiConfig.baseUrl}${path}`, init);
  } catch {
    throw new IncidentApiError("The incident service could not be reached.", 0);
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: string | { message?: string } }
      | null;
    const detail = typeof body?.detail === "string" ? body.detail : body?.detail?.message;
    throw new IncidentApiError(detail ?? "The incident service returned an error.", response.status);
  }

  return (await response.json()) as T;
}

export async function listIncidents(filters: IncidentListFilters = {}): Promise<IncidentListResponse> {
  const params = new URLSearchParams({ limit: "100" });
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  return parseIncidentList(await request<unknown>(`/incidents?${params.toString()}`));
}

export async function getIncident(incidentId: string): Promise<Incident> {
  return parseIncident(await request<unknown>(`/incidents/${encodeURIComponent(incidentId)}`));
}

export async function createIncidentReport(report: IncidentReport): Promise<Incident> {
  return parseIncident(
    await request<unknown>("/incidents/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    }),
  );
}
