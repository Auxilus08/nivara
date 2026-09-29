"use client";

import { useEffect, useMemo } from "react";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  Rectangle,
  TileLayer,
  useMap,
} from "react-leaflet";
import L from "leaflet";

import type { Coordinate, HeatmapResponse, RouteCandidate } from "@/lib/navigation";

export type NivaraMapProps = {
  currentLocation: Coordinate | null;
  destination: Coordinate | null;
  routes: RouteCandidate[];
  selectedRouteId: string | null;
  heatmap: HeatmapResponse | null;
};

type LeafletPosition = [number, number];

const DEFAULT_CENTER: LeafletPosition = [20, 0];

const currentLocationIcon = L.divIcon({
  className: "nivara-map-marker nivara-map-marker-current",
  html: '<span aria-hidden="true"></span>',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

const destinationIcon = L.divIcon({
  className: "nivara-map-marker nivara-map-marker-destination",
  html: '<span aria-hidden="true"></span>',
  iconSize: [24, 24],
  iconAnchor: [12, 22],
});

function toPosition(coordinate: Coordinate | null): LeafletPosition | null {
  if (
    !coordinate ||
    !Number.isFinite(coordinate.latitude) ||
    !Number.isFinite(coordinate.longitude) ||
    coordinate.latitude < -90 ||
    coordinate.latitude > 90 ||
    coordinate.longitude < -180 ||
    coordinate.longitude > 180
  ) {
    return null;
  }
  return [coordinate.latitude, coordinate.longitude];
}

function toPositions(coordinates: Coordinate[] | undefined): LeafletPosition[] {
  return (coordinates ?? []).map(toPosition).filter((position): position is LeafletPosition => position !== null);
}

function routeColor(route: RouteCandidate, selectedRouteId: string | null) {
  return route.route_id === selectedRouteId ? "#4f46e5" : "#94a3b8";
}

function heatmapColor(riskLevel: string) {
  if (riskLevel === "high") return "#dc2626";
  if (riskLevel === "elevated") return "#f97316";
  if (riskLevel === "moderate") return "#eab308";
  return "#22c55e";
}

function MapViewportController({
  routes,
  selectedRouteId,
  currentLocation,
  destination,
}: Pick<NivaraMapProps, "routes" | "selectedRouteId" | "currentLocation" | "destination">) {
  const map = useMap();
  const selectedRoute = routes.find((route) => route.route_id === selectedRouteId);
  const selectedPositions = toPositions(selectedRoute?.geometry?.coordinates);
  const currentPosition = toPosition(currentLocation);
  const destinationPosition = toPosition(destination);
  const focusPositions = selectedPositions.length > 0
    ? selectedPositions
    : [currentPosition, destinationPosition].filter(
        (position): position is LeafletPosition => position !== null,
      );
  const focusKey = focusPositions.map((position) => position.join(",")).join(";");

  useEffect(() => {
    if (focusPositions.length > 1) {
      map.fitBounds(L.latLngBounds(focusPositions), { padding: [32, 32], maxZoom: 16 });
    } else if (focusPositions.length === 1) {
      map.setView(focusPositions[0], Math.max(map.getZoom(), 13));
    }
    // focusKey represents the complete set of positions used for this viewport.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusKey, map]);

  return null;
}

function HeatmapCells({ heatmap }: { heatmap: HeatmapResponse }) {
  const rows = Math.max(heatmap.rows, 1);
  const columns = Math.max(heatmap.columns, 1);
  const latitudeStep = (heatmap.bounds.max_latitude - heatmap.bounds.min_latitude) / rows;
  const longitudeStep = (heatmap.bounds.max_longitude - heatmap.bounds.min_longitude) / columns;

  if (!Number.isFinite(latitudeStep) || !Number.isFinite(longitudeStep) || latitudeStep <= 0 || longitudeStep <= 0) {
    return null;
  }

  return (
    <>
      {heatmap.points.map((point) => {
        const position = toPosition(point);
        if (!position) return null;
        const halfLatitude = latitudeStep / 2;
        const halfLongitude = longitudeStep / 2;
        const bounds: [[number, number], [number, number]] = [
          [Math.max(heatmap.bounds.min_latitude, point.latitude - halfLatitude), Math.max(heatmap.bounds.min_longitude, point.longitude - halfLongitude)],
          [Math.min(heatmap.bounds.max_latitude, point.latitude + halfLatitude), Math.min(heatmap.bounds.max_longitude, point.longitude + halfLongitude)],
        ];
        const color = heatmapColor(point.risk_level);
        return (
          <Rectangle
            key={`${point.latitude}-${point.longitude}`}
            bounds={bounds}
            pathOptions={{ color, fillColor: color, fillOpacity: 0.22, weight: 1 }}
          >
            <Popup>
              <span>{point.risk_level} contextual safety indicators</span>
            </Popup>
          </Rectangle>
        );
      })}
    </>
  );
}

export function NivaraMap({
  currentLocation,
  destination,
  routes,
  selectedRouteId,
  heatmap,
}: NivaraMapProps) {
  const initialCenter = useMemo(
    () => toPosition(currentLocation) ?? toPosition(destination) ?? DEFAULT_CENTER,
    [currentLocation, destination],
  );
  const currentPosition = toPosition(currentLocation);
  const destinationPosition = toPosition(destination);
  const renderableRoutes = routes
    .map((route) => ({ route, positions: toPositions(route.geometry?.coordinates) }))
    .filter(({ positions }) => positions.length > 1);

  return (
    <div className="relative h-full min-h-[320px] w-full overflow-hidden rounded-xl bg-slate-200">
      <MapContainer center={initialCenter} zoom={2} scrollWheelZoom className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapViewportController
          routes={routes}
          selectedRouteId={selectedRouteId}
          currentLocation={currentLocation}
          destination={destination}
        />
        {heatmap && <HeatmapCells heatmap={heatmap} />}
        {renderableRoutes.map(({ route, positions }) => {
          const selected = route.route_id === selectedRouteId;
          return (
            <Polyline
              key={route.route_id}
              positions={positions}
              pathOptions={{
                color: routeColor(route, selectedRouteId),
                opacity: selected ? 0.95 : 0.55,
                weight: selected ? 6 : 4,
                dashArray: selected ? undefined : "8 10",
              }}
            >
              <Popup>{selected ? "Selected route" : "Alternative route"}</Popup>
            </Polyline>
          );
        })}
        {currentPosition && (
          <Marker position={currentPosition} icon={currentLocationIcon}>
            <Popup>Current location</Popup>
          </Marker>
        )}
        {destinationPosition && (
          <Marker position={destinationPosition} icon={destinationIcon}>
            <Popup>Selected destination</Popup>
          </Marker>
        )}
      </MapContainer>
      {renderableRoutes.length === 0 && (
        <div className="pointer-events-none absolute left-1/2 top-4 z-[500] -translate-x-1/2 rounded-full bg-white/95 px-3 py-2 text-center text-xs text-slate-600 shadow-sm">
          Select a destination and request a route to display it here.
        </div>
      )}
    </div>
  );
}

export default NivaraMap;
