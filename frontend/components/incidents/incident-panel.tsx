"use client";

import { FormEvent, useEffect, useState } from "react";

import { Card, CardContent } from "@/components/ui/card";
import {
  createIncidentReport,
  getIncident,
  incidentCategories,
  incidentConfidenceLevels,
  incidentSeverities,
  incidentStatuses,
  listIncidents,
  type Incident,
  type IncidentCategory,
  type IncidentConfidenceLevel,
  type IncidentListFilters,
  type IncidentSeverity,
  type IncidentStatus,
} from "@/lib/incidents";
import type { Coordinate } from "@/lib/navigation";

type IncidentPanelProps = {
  currentLocation: Coordinate | null;
};

const categoryLabels: Record<IncidentCategory, string> = {
  harassment: "Harassment",
  theft: "Theft",
  suspicious_activity: "Suspicious activity",
  poor_lighting: "Poor lighting",
  unsafe_isolated_area: "Unsafe/isolated area indicators",
  other: "Other",
};

const labelize = (value: string) => value.replaceAll("_", " ");

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Time unavailable" : date.toLocaleString();
}

function approximateLocation(incident: Incident) {
  return `Near ${incident.latitude.toFixed(2)}, ${incident.longitude.toFixed(2)}`;
}

function toIso(value: string) {
  return value ? new Date(value).toISOString() : undefined;
}

export function IncidentPanel({ currentLocation }: IncidentPanelProps) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reportSuccess, setReportSuccess] = useState<string | null>(null);
  const [listCount, setListCount] = useState(0);
  const [filters, setFilters] = useState<IncidentListFilters>({});
  const [report, setReport] = useState({
    category: "harassment" as IncidentCategory,
    description: "",
    latitude: "",
    longitude: "",
    occurredAt: "",
    severity: "medium" as IncidentSeverity,
  });

  async function loadIncidents(nextFilters = filters) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listIncidents(nextFilters);
      setIncidents(response.items);
      setListCount(response.count);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Incident activity could not be loaded.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadIncidents();
    // The initial request intentionally runs once; filters are applied by the filter form.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateFilter(key: keyof IncidentListFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value || undefined }));
  }

  async function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadIncidents(filters);
  }

  function useCurrentLocation() {
    if (!currentLocation) {
      setError("Use current location above before filling the report location.");
      return;
    }
    setReport((current) => ({
      ...current,
      latitude: String(currentLocation.latitude),
      longitude: String(currentLocation.longitude),
    }));
  }

  async function submitReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setReportSuccess(null);
    const latitude = Number(report.latitude);
    const longitude = Number(report.longitude);
    const description = report.description.trim();
    if (!description || description.length < 10) {
      setError("Please provide at least 10 characters describing the reported incident.");
      return;
    }
    if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90 || !Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
      setError("Enter a valid latitude between -90 and 90 and longitude between -180 and 180.");
      return;
    }
    if (report.occurredAt && Number.isNaN(new Date(report.occurredAt).getTime())) {
      setError("Enter a valid incident time or leave the time blank.");
      return;
    }
    const occurredAt = toIso(report.occurredAt);
    setIsSubmitting(true);
    try {
      await createIncidentReport({
        category: report.category,
        description,
        latitude,
        longitude,
        severity: report.severity,
        ...(occurredAt ? { occurred_at: occurredAt } : {}),
      });
      setReport((current) => ({ ...current, description: "", occurredAt: "" }));
      setReportSuccess("Your community report was submitted for review and is currently unverified.");
      await loadIncidents(filters);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The incident report could not be submitted.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function selectIncident(incidentId: string) {
    setError(null);
    try {
      setSelectedIncident(await getIncident(incidentId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Incident details could not be loaded.");
    }
  }

  return (
    <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]" aria-label="Community incident information">
      <Card>
        <CardContent>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-indigo-600">Community reports</p>
          <h2 className="mt-2 text-2xl font-semibold">Report an incident</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Share contextual information that may help others understand incident activity. Reports begin as unverified community reports.
          </p>
          <form className="mt-5 space-y-4" onSubmit={submitReport}>
            <div>
              <label className="text-sm font-medium" htmlFor="incident-category">Category</label>
              <select id="incident-category" value={report.category} onChange={(event) => setReport({ ...report, category: event.target.value as IncidentCategory })} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm">
                {incidentCategories.map((category) => <option key={category} value={category}>{categoryLabels[category]}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium" htmlFor="incident-description">What happened?</label>
              <textarea id="incident-description" value={report.description} onChange={(event) => setReport({ ...report, description: event.target.value })} minLength={10} maxLength={2000} required rows={4} placeholder="Describe the reported incident without personal contact details." className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none ring-indigo-200 focus:ring-2" />
              <p className="mt-1 text-xs text-slate-500">At least 10 characters. Please do not include names, phone numbers, or other private contact details.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium" htmlFor="incident-latitude">Latitude</label>
                <input id="incident-latitude" inputMode="decimal" value={report.latitude} onChange={(event) => setReport({ ...report, latitude: event.target.value })} required placeholder="12.9716" className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="text-sm font-medium" htmlFor="incident-longitude">Longitude</label>
                <input id="incident-longitude" inputMode="decimal" value={report.longitude} onChange={(event) => setReport({ ...report, longitude: event.target.value })} required placeholder="77.5946" className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" />
              </div>
            </div>
            <button type="button" onClick={useCurrentLocation} className="text-sm font-medium text-indigo-700">Use current location</button>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="text-sm font-medium" htmlFor="incident-severity">Severity</label>
                <select id="incident-severity" value={report.severity} onChange={(event) => setReport({ ...report, severity: event.target.value as IncidentSeverity })} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm">
                  {incidentSeverities.map((severity) => <option key={severity} value={severity}>{labelize(severity)}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium" htmlFor="incident-occurred-at">When did it occur? (optional)</label>
                <input id="incident-occurred-at" type="datetime-local" value={report.occurredAt} onChange={(event) => setReport({ ...report, occurredAt: event.target.value })} className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm" />
              </div>
            </div>
            <button type="submit" disabled={isSubmitting} className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white disabled:cursor-wait disabled:opacity-60">{isSubmitting ? "Submitting report…" : "Submit community report"}</button>
          </form>
          {reportSuccess && <p role="status" className="mt-4 rounded-xl bg-emerald-50 px-3 py-2.5 text-sm text-emerald-800">{reportSuccess}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-indigo-600">Incident activity</p>
              <h2 className="mt-2 text-2xl font-semibold">Community reports nearby</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">Contextual safety information based on available reported incidents.</p>
            </div>
            <button type="button" onClick={() => void loadIncidents()} className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700">Refresh</button>
          </div>
          <form className="mt-5 grid gap-3 sm:grid-cols-2" onSubmit={applyFilters}>
            <label className="text-xs font-medium text-slate-600">Category
              <select value={filters.category ?? ""} onChange={(event) => updateFilter("category", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm">
                <option value="">All categories</option>
                {incidentCategories.map((category) => <option key={category} value={category}>{categoryLabels[category]}</option>)}
              </select>
            </label>
            <label className="text-xs font-medium text-slate-600">Severity
              <select value={filters.severity ?? ""} onChange={(event) => updateFilter("severity", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm">
                <option value="">All severities</option>
                {incidentSeverities.map((severity) => <option key={severity} value={severity}>{labelize(severity)}</option>)}
              </select>
            </label>
            <label className="text-xs font-medium text-slate-600">Status
              <select value={filters.status ?? ""} onChange={(event) => updateFilter("status", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm">
                <option value="">All statuses</option>
                {incidentStatuses.map((status) => <option key={status} value={status}>{labelize(status)}</option>)}
              </select>
            </label>
            <label className="text-xs font-medium text-slate-600">Confidence
              <select value={filters.confidence_level ?? ""} onChange={(event) => updateFilter("confidence_level", event.target.value)} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm">
                <option value="">All confidence levels</option>
                {incidentConfidenceLevels.map((level) => <option key={level} value={level}>{labelize(level)}</option>)}
              </select>
            </label>
            <label className="text-xs font-medium text-slate-600">From time
              <input type="datetime-local" value={filters.occurred_from?.slice(0, 16) ?? ""} onChange={(event) => updateFilter("occurred_from", toIso(event.target.value) ?? "")} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm" />
            </label>
            <label className="text-xs font-medium text-slate-600">To time
              <input type="datetime-local" value={filters.occurred_to?.slice(0, 16) ?? ""} onChange={(event) => updateFilter("occurred_to", toIso(event.target.value) ?? "")} className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm" />
            </label>
            <button type="submit" className="sm:col-span-2 rounded-lg bg-slate-900 px-3 py-2.5 text-sm font-medium text-white">Apply incident filters</button>
          </form>

          {error && <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-3 py-2.5 text-sm text-rose-700">{error}</p>}
          {isLoading && <p className="mt-5 text-sm text-slate-500" role="status">Loading incident activity…</p>}
          {!isLoading && incidents.length === 0 && <p className="mt-5 rounded-xl bg-slate-50 px-3 py-4 text-sm text-slate-500">No reported incidents match these filters.</p>}
          {!isLoading && incidents.length > 0 && <>
            <p className="mt-5 text-xs text-slate-500">Showing {incidents.length} of {listCount} reported incident(s).</p>
            <div className="mt-3 space-y-3">
              {incidents.map((incident) => (
                <button type="button" key={incident.id} onClick={() => void selectIncident(incident.id)} className="w-full rounded-xl border border-slate-200 p-4 text-left transition hover:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-300">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-slate-900">{categoryLabels[incident.category]}</span>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">{labelize(incident.severity)}</span>
                    <span className="rounded-full bg-amber-50 px-2 py-1 text-xs text-amber-800">{labelize(incident.confidence.level)}</span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm text-slate-600">{incident.description}</p>
                  <p className="mt-2 text-xs text-slate-500">{approximateLocation(incident)} · {formatDate(incident.occurred_at)} · {labelize(incident.status)}</p>
                </button>
              ))}
            </div>
          </>}
        </CardContent>
      </Card>

      {selectedIncident && (
        <Card className="lg:col-span-2 border-indigo-100">
          <CardContent>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.16em] text-indigo-600">Reported incident</p>
                <h2 className="mt-2 text-xl font-semibold">{categoryLabels[selectedIncident.category]}</h2>
              </div>
              <button type="button" onClick={() => setSelectedIncident(null)} className="text-sm font-medium text-slate-500">Close</button>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-700">{selectedIncident.description}</p>
            <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2 lg:grid-cols-4">
              <p>Severity: <span className="font-medium">{labelize(selectedIncident.severity)}</span></p>
              <p>Status: <span className="font-medium">{labelize(selectedIncident.status)}</span></p>
              <p>Confidence: <span className="font-medium">{labelize(selectedIncident.confidence.level)}</span></p>
              <p>Location: <span className="font-medium">{approximateLocation(selectedIncident)}</span></p>
              <p className="sm:col-span-2 lg:col-span-4">Occurred: <span className="font-medium">{formatDate(selectedIncident.occurred_at)}</span></p>
            </div>
            <p className="mt-4 text-xs text-slate-500">This is contextual incident information based on a reported event. It does not establish that an area is safe or dangerous.</p>
          </CardContent>
        </Card>
      )}
    </section>
  );
}
