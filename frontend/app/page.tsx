"use client";

import { FormEvent, useState } from "react";
import { LocateFixed, Map, ShieldCheck } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import {
  calculateRoutes,
  calculateHeatmap,
  type Coordinate,
  type HeatmapPoint,
  type HeatmapResponse,
  type HeatmapViewport,
  type RouteMode,
  type RouteResponse,
} from "@/lib/navigation";

function formatCoordinate(coordinate: Coordinate | null) {
  if (!coordinate) return "Location not selected";
  return `${coordinate.latitude.toFixed(5)}, ${coordinate.longitude.toFixed(5)}`;
}

function parseDestination(value: string): Coordinate | null {
  const [latitudeText, longitudeText] = value.split(",").map((part) => part.trim());
  const latitude = Number(latitudeText);
  const longitude = Number(longitudeText);
  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    latitude < -90 ||
    latitude > 90 ||
    longitude < -180 ||
    longitude > 180
  ) {
    return null;
  }
  return { latitude, longitude };
}

function formatMode(mode: RouteMode) {
  return mode === "safety_priority" ? "Safety Priority" : mode[0].toUpperCase() + mode.slice(1);
}

function describeMode(mode: RouteMode) {
  if (mode === "fastest") return "Prioritizes shorter travel time while retaining available safety indicators.";
  if (mode === "balanced") return "Balances travel time with available safety indicators.";
  return "Places greater weight on available safety indicators than travel time.";
}

function heatmapViewport(coordinate: Coordinate): HeatmapViewport {
  return {
    min_latitude: Math.max(-90, coordinate.latitude - 0.05),
    min_longitude: Math.max(-180, coordinate.longitude - 0.05),
    max_latitude: Math.min(90, coordinate.latitude + 0.05),
    max_longitude: Math.min(180, coordinate.longitude + 0.05),
  };
}

function heatmapColor(point: HeatmapPoint) {
  if (point.risk_level === "high") return "#dc2626";
  if (point.risk_level === "elevated") return "#f97316";
  if (point.risk_level === "moderate") return "#eab308";
  return "#22c55e";
}

export default function HomePage() {
  const [currentLocation, setCurrentLocation] = useState<Coordinate | null>(null);
  const [destination, setDestination] = useState("");
  const [mode, setMode] = useState<RouteMode>("fastest");
  const [routeResponse, setRouteResponse] = useState<RouteResponse | null>(null);
  const [isLocating, setIsLocating] = useState(false);
  const [isRouting, setIsRouting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [isLoadingHeatmap, setIsLoadingHeatmap] = useState(false);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);

  function requestLocation() {
    if (!navigator.geolocation) {
      setError("Location is not available in this browser.");
      return;
    }
    setIsLocating(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setCurrentLocation({ latitude: coords.latitude, longitude: coords.longitude });
        setHeatmap(null);
        setHeatmapError(null);
        setIsLocating(false);
      },
      (positionError) => {
        setIsLocating(false);
        setError(
          positionError.code === 1
            ? "Location permission was denied. You can enable it in browser settings."
            : "Your current location could not be determined.",
        );
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 30000 },
    );
  }

  async function loadHeatmap() {
    if (!currentLocation) {
      setHeatmapError("Use your current location to define the map viewport.");
      return;
    }
    setIsLoadingHeatmap(true);
    setHeatmapError(null);
    try {
      setHeatmap(await calculateHeatmap(heatmapViewport(currentLocation)));
    } catch (heatmapRequestError) {
      setHeatmapError(
        heatmapRequestError instanceof Error
          ? heatmapRequestError.message
          : "The contextual indicators could not be loaded.",
      );
    } finally {
      setIsLoadingHeatmap(false);
    }
  }

  async function submitRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setRouteResponse(null);
    const parsedDestination = parseDestination(destination);
    if (!currentLocation) {
      setError("Select your current location before requesting a route.");
      return;
    }
    if (!parsedDestination) {
      setError("Enter a destination as latitude, longitude.");
      return;
    }
    setIsRouting(true);
    try {
      setRouteResponse(await calculateRoutes(currentLocation, parsedDestination, mode));
    } catch (routeError) {
      setError(routeError instanceof Error ? routeError.message : "Route lookup failed.");
    } finally {
      setIsRouting(false);
    }
  }

  return (
    <main className="min-h-screen px-6 py-8 sm:px-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-8">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-indigo-600 p-2 text-white"><ShieldCheck size={22} /></div>
            <span className="text-xl font-semibold tracking-tight">Nivara</span>
          </div>
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">Navigation foundation</span>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <Card className="overflow-hidden border-slate-200">
            <div className="flex h-[420px] flex-col items-center justify-center bg-slate-100 p-6">
              <div className="relative flex min-h-0 w-full flex-1 items-center justify-center overflow-hidden rounded-xl border border-dashed border-slate-300 bg-[radial-gradient(circle_at_center,_#ffffff_0,_#f1f5f9_65%)]">
                <Map className="text-slate-300" size={80} strokeWidth={1} />
                {heatmap && heatmap.points.map((point) => {
                  const left = ((point.longitude - heatmap.bounds.min_longitude) / (heatmap.bounds.max_longitude - heatmap.bounds.min_longitude)) * 100;
                  const top = (1 - ((point.latitude - heatmap.bounds.min_latitude) / (heatmap.bounds.max_latitude - heatmap.bounds.min_latitude))) * 100;
                  return (
                    <div
                      key={`${point.latitude}-${point.longitude}`}
                      className="absolute h-12 w-12 -translate-x-1/2 -translate-y-1/2 rounded-full opacity-60 blur-sm"
                      style={{ left: `${left}%`, top: `${top}%`, backgroundColor: heatmapColor(point) }}
                      title={`${point.risk_level} contextual risk indicators, score ${point.risk_score}`}
                    />
                  );
                })}
                {currentLocation && (
                  <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center gap-2 rounded-full bg-indigo-600 px-3 py-2 text-xs font-medium text-white shadow-lg">
                    <LocateFixed size={14} /> Current location
                  </div>
                )}
                <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between gap-3">
                  <span className="rounded bg-white/90 px-2 py-1 text-xs text-slate-500 shadow-sm">Provider map surface pending</span>
                  <button type="button" onClick={loadHeatmap} disabled={isLoadingHeatmap || !currentLocation} className="rounded-lg bg-white/95 px-3 py-2 text-xs font-medium text-indigo-700 shadow-sm disabled:cursor-not-allowed disabled:opacity-50">
                    {isLoadingHeatmap ? "Loading indicators…" : "Show contextual indicators"}
                  </button>
                </div>
              </div>
              <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs font-semibold text-slate-700">Contextual risk indicators</p>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
                  {[['#22c55e', 'LOW'], ['#eab308', 'MODERATE'], ['#f97316', 'ELEVATED'], ['#dc2626', 'HIGH']].map(([color, label]) => (
                    <span key={label} className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />{label}</span>
                  ))}
                </div>
                {heatmapError && <p role="alert" className="mt-2 text-xs text-rose-700">{heatmapError}</p>}
                {heatmap && heatmap.points.length === 0 && <p className="mt-2 text-xs text-slate-500">No incident-derived indicators were returned for this viewport.</p>}
                {heatmap && heatmap.points.length > 0 && <p className="mt-2 text-xs text-slate-500">{heatmap.incident_count} incident-derived indicator(s) aggregated into the viewport. {heatmap.disclaimer}</p>}
              </div>
            </div>
          </Card>

          <Card className="border-indigo-100">
            <CardContent>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-indigo-600">Plan a journey</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight">Plan journeys with more context.</h1>
              <p className="mt-3 text-sm leading-6 text-slate-600">Route estimates will be enriched with contextual safety indicators. They are not guarantees of what will happen.</p>
              <form className="mt-6 space-y-4" onSubmit={submitRoute}>
                <div>
                  <label className="text-sm font-medium" htmlFor="destination">Destination coordinates</label>
                  <input id="destination" value={destination} onChange={(event) => setDestination(event.target.value)} placeholder="12.9352, 77.6245" className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none ring-indigo-200 focus:ring-2" />
                  <p className="mt-1 text-xs text-slate-500">Geocoded destination search will use the provider adapter when selected.</p>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5 text-sm">
                  <span className="text-slate-600">{formatCoordinate(currentLocation)}</span>
                  <button type="button" onClick={requestLocation} className="font-medium text-indigo-700" disabled={isLocating}>{isLocating ? "Locating…" : "Use current location"}</button>
                </div>
                <div>
                  <label className="text-sm font-medium" htmlFor="mode">Route preference</label>
                  <select id="mode" value={mode} onChange={(event) => setMode(event.target.value as RouteMode)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm">
                    <option value="fastest">Fastest</option>
                    <option value="balanced">Balanced</option>
                    <option value="safety_priority">Safety priority</option>
                  </select>
                  <p className="mt-1 text-xs text-slate-500">{describeMode(mode)}</p>
                </div>
                <button type="submit" disabled={isRouting} className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white disabled:cursor-wait disabled:opacity-60">{isRouting ? "Requesting route…" : "Request route"}</button>
              </form>
              {error && <p role="alert" className="mt-4 rounded-xl bg-rose-50 px-3 py-2.5 text-sm text-rose-700">{error}</p>}
            </CardContent>
          </Card>
        </section>

        {routeResponse && (
          <Card>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-semibold">Route results</h2>
                  <p className="mt-1 text-sm text-slate-500">{routeResponse.routes.length} candidate route(s), mode: {formatMode(routeResponse.mode)}</p>
                </div>
                <ShieldCheck className="text-indigo-600" size={22} />
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {routeResponse.routes.map((route) => (
                  <div key={route.route_id} className={`rounded-xl border p-4 ${route.route_id === routeResponse.selected_route_id ? "border-indigo-400 bg-indigo-50/50" : "border-slate-200"}`}>
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium">{route.route_id}</p>
                      {route.route_id === routeResponse.selected_route_id && <span className="rounded-full bg-indigo-100 px-2 py-1 text-xs font-medium text-indigo-700">Selected for {formatMode(routeResponse.mode)}</span>}
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{(route.distance_meters / 1000).toFixed(1)} km · {Math.ceil(route.estimated_duration_seconds / 60)} min</p>
                    {route.normalized_travel_score !== null && <p className="mt-2 text-xs text-slate-500">Travel-time score: {route.normalized_travel_score.toFixed(1)} · Comparison cost: {route.comparison_cost?.toFixed(1) ?? "—"}</p>}
                    {route.safety_assessment ? (
                      <div className="mt-2 space-y-1 text-xs text-slate-600">
                        <p>Contextual risk indicators: {route.safety_assessment.risk_level} ({route.safety_assessment.risk_score}/100)</p>
                        <p>{route.safety_assessment.factors.find((factor) => factor.contribution > 0)?.description ?? "Limited incident activity indicators were available."}</p>
                      </div>
                    ) : <p className="mt-2 text-xs text-slate-500">Incident-derived safety indicators were unavailable for this route.</p>}
                  </div>
                ))}
              </div>
              <p className="mt-4 text-xs text-slate-500">{routeResponse.comparison_explanation}</p>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}
