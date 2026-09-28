# Nivara Agent Transfer

## Current Status

Foundation, incident domain, deterministic Safety Engine, provider-neutral
navigation foundation, the first concrete external routing adapter, route
comparison with incident-derived safety enrichment, the explicit FASTEST mode
experience, the explicit BALANCED mode experience, the explicit
SAFETY_PRIORITY mode experience, and the first bounded contextual safety
heatmap are implemented. No live provider key or live PostGIS database is
configured in this environment.

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
- T018 Balanced mode
- T019 Safety Priority mode
- T020 Safety heatmap
- T030 Incident model
- T031 Incident listing
- T032 Incident spatial queries
- T033 Community report creation
- T034 Community report validation
- T035 Confidence model
- T036 Incident filtering

T012 destination search remains incomplete.

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
- `backend/app/api/routes/safety.py` exposes the bounded
  `GET /api/v1/safety/heatmap` endpoint. It requires a 0.02–2 degree viewport
  and accepts a 2–12 by 2–12 coarse grid.
- `IncidentRepository.list_in_bounds` performs the bounded PostGIS envelope
  query. `IncidentService.get_heatmap` deterministically bins incidents into
  occupied cells and sends each cell's `IncidentSignalContext` through the
  existing SafetyEngine.
- `frontend/lib/navigation.ts` contains typed heatmap contracts and the API
  client. `frontend/app/page.tsx` renders a lightweight CSS indicator overlay,
  contextual legend, loading/error/no-data states, and the canonical
  disclaimer. No map-rendering dependency was added because the repository has
  no existing map library and T020 does not require selecting one.

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

BALANCED is explicitly described as balancing travel time with available safety
indicators. It uses time/safety weights of 0.55/0.45 with the same normalized
duration and SafetyEngine risk score used by the comparison service. Tests cover
both directions of the trade-off, equal-duration safety selection, equal-cost
tie behavior, single-candidate behavior, and safety assessment visibility.

SAFETY_PRIORITY is explicitly described as placing greater weight on available
safety indicators than travel time. It uses time/safety weights of 0.25/0.75.
Tests cover slower lower-risk selection, large travel-time penalties, equal-
duration risk selection, deterministic ties, single candidates, assessment
visibility, and the API contract.

## API

Implemented:

- `POST /api/v1/routes`
- `GET /api/v1/safety/heatmap`

If the routing key is missing or rejected, the endpoint returns a provider-
neutral `503` configuration error. Rate limits return `429`, timeouts return
`504`, and provider HTTP or response-shape failures return `502`.

Successful responses include `selected_route_id`, normalized travel-time and
comparison-cost fields per candidate, and optional `safety_assessment` values.
If any candidate lacks incident context, comparison falls back to normalized
travel time for all candidates and explains that safety indicators were
unavailable; missing context is never treated as zero risk.

## Heatmap Contract and Limitations

The heatmap returns occupied cell centers with `risk_score`, `risk_level`,
`incident_count`, and assessment `confidence`, plus bounds, grid dimensions,
total incident count, and the contextual disclaimer. It does not return
incident IDs, descriptions, reporter identity, or moderation fields. No-data
cells are omitted and no score is fabricated for them. The visualization is
contextual incident activity, not a prediction or guarantee of safety.

## Verification Performed

- `python3 -m pip install -e '.[test]' --user` from `backend/` — passed
- `pytest -q` from `backend/` — passed, 76 tests
- `python -m compileall backend/app` — passed
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
- Heatmap points are occupied coarse cells centered on aggregated incident
  locations; the frontend overlay is illustrative and does not provide map
  tiles or route selection.

## Exact Next Task

T037 — Build the incident UI on top of the incident and heatmap API contracts,
preserving contextual language and privacy boundaries.
