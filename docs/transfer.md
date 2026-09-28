# Nivara Agent Transfer

## Current Status

Foundation, incident domain, deterministic Safety Engine, provider-neutral
navigation foundation, the first concrete external routing adapter, route
comparison with incident-derived safety enrichment, and the explicit FASTEST
mode experience are implemented. No live
provider key or live PostGIS database is configured in this environment.

## Last Completed Tasks

- T001 Repository foundation
- T002 Frontend foundation
- T003 Backend foundation
- T004 Database foundation
- T005 Configuration/environment foundation
- T006 API foundation
- T007 Testing foundation
- T010 Map integration foundation
- T011 Current location
- T013 Routing integration
- T014 Route normalization
- T015 Safety scoring
- T016 Route comparison
- T017 Fastest mode
- T030 Incident model
- T031 Incident listing
- T032 Incident spatial queries
- T033 Community report creation
- T034 Community report validation
- T035 Confidence model
- T036 Incident filtering

T012 destination search and T018–T020 route modes/heatmap remain incomplete.

## Navigation Architecture

Backend:

- `backend/app/schemas/routes.py` defines validated coordinates, route modes,
  provider-neutral geometry, route candidates, route responses, and future
  destination suggestions.
- `backend/app/providers/routing.py` defines `RoutingProvider` and
  `GeocodingProvider` protocols, normalized `ProviderRoute`, explicit provider
  errors, and the openrouteservice adapter.
- `backend/app/services/routes.py` calls a provider and normalizes results into
  Nivara-owned `RouteResponse` objects.
- `backend/app/api/routes/routes.py` exposes `POST /api/v1/routes` and maps
  provider failures to safe status codes without leaking implementation
  details.
- `OpenRouteServiceProvider` calls the documented Directions GeoJSON endpoint.
  Missing or rejected credentials fail explicitly; no route data is fabricated.

Frontend:

- `frontend/lib/navigation.ts` defines the frontend route contract and API
  client without exposing routing credentials.
- `frontend/app/page.tsx` provides the minimum navigation shell: map surface
  placeholder, browser geolocation, coordinate-based destination input, route
  mode selection, loading/error states, and normalized route result rendering.
- Destination search is intentionally not implemented; the geocoding protocol
  remains available for a future provider adapter.

## Provider Configuration

`.env.example` now documents:

- `ROUTING_PROVIDER=openrouteservice`
- `ROUTING_API_KEY=`

The adapter uses `POST https://api.openrouteservice.org/v2/directions/driving-car/geojson`,
the server-side `Authorization` header, and a JSON body with coordinates in
`[longitude, latitude]` order. GeoJSON `LineString` coordinates are normalized
back to Nivara's latitude/longitude coordinate objects. Summary distance is
meters and duration is rounded to integer seconds.

The adapter requests up to three provider-supported alternatives. It returns
only candidates actually provided by OpenRouteService; it does not fabricate
alternatives. Provider route modes are not themselves safety-aware.

## Safety Integration Boundary

The route contract includes an optional `safety_assessment` field so future
navigation work can enrich normalized candidates with the existing
`IncidentSignalContext -> SafetyEngine -> SafetyAssessment` flow. T016 now
collects incident indicators through a PostGIS route corridor, enriches each
candidate with an assessment when geometry and context are available, and
compares candidates using the configured objective. The Safety Engine remains
database-independent and is not called from route handlers.

The corridor defaults to `ROUTE_CORRIDOR_RADIUS_METERS=100` and is bounded to
25–1000 metres. Route comparison uses normalized duration divided by the
slowest candidate, multiplied by 100, then combines it with risk score:
`time_weight * normalized_time + safety_weight * risk_score`.
Weights are FASTEST 0.90/0.10, BALANCED 0.55/0.45, and SAFETY_PRIORITY
0.25/0.75 for time/safety. These are contextual selection estimates, not
guarantees of safety.

FASTEST is explicitly described as prioritizing shorter travel time while
retaining available safety indicators. Comparison ties use lower duration, then
lexicographically lower `route_id`, after comparison cost.

## API

Implemented:

- `POST /api/v1/routes`

If the routing key is missing or rejected, the endpoint returns a provider-
neutral `503` configuration error. Rate limits return `429`, timeouts return
`504`, and provider HTTP or response-shape failures return `502`.

Successful responses include `selected_route_id`, normalized travel-time and
comparison-cost fields per candidate, and optional `safety_assessment` values.
If any candidate lacks incident context, comparison falls back to normalized
travel time for all candidates and explains that safety indicators were
unavailable; missing context is never treated as zero risk.

## Verification Performed

- `python3 -m pip install -e '.[test]' --user` from `backend/` — passed
- `pytest -q` from `backend/` — passed, 53 tests
- `python3 -m compileall -q app` — passed
- `git diff --check` — passed
- `pnpm typecheck` from `frontend/` — passed
- `pnpm build` from `frontend/` — passed

Provider tests use mocked HTTP clients. No live map/routing provider
integration was run or claimed because no credential was configured.

## Known Limitations

- No live routing credential is configured in this environment.
- No live PostgreSQL/PostGIS integration verification was performed.
- No live map tiles or external geocoding/search.
- Destination entry currently accepts latitude/longitude rather than place
  search.
- Provider route modes are validated and carried through the contract; route
  comparison applies the Nivara time/safety objective after provider results
  are normalized.
- Corridor context is a simple LineString proximity aggregate and does not yet
  account for route segment length, isolation, lighting, activity, or other
  future signals.
- The map surface is a frontend shell, not a custom map engine.

## Exact Next Task

T018 — Validate the BALANCED mode experience using the existing comparison
service. Preserve provider-neutral contracts and contextual, non-guaranteed
safety language.
