# Nivara Agent Transfer

## Current Status

Foundation, incident domain, deterministic Safety Engine, provider-neutral
navigation foundation, the first concrete external routing adapter, route
comparison with incident-derived safety enrichment, the explicit FASTEST mode
experience, the explicit BALANCED mode experience, the explicit
SAFETY_PRIORITY mode experience, and the first bounded contextual safety
heatmap are implemented. The frontend incident reporting, browsing/filtering,
and detail experience is also implemented. No live provider key or live
PostGIS database is configured in this environment.

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
- T012 Destination search
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
- T037 Incident UI
- T100 Navigation integration
- T101 Safety engine integration
- T102 Community reports integration

The primary demonstration flow now connects browser location, destination
search/selection, backend route comparison, contextual heatmap indicators, and
the independent incident panel. Route mode changes recalculate through the
backend; no safety calculation was moved into the frontend.

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
- `frontend/lib/geocoding.ts` defines the typed destination search client and
  validates provider-neutral response shapes.
- `frontend/app/page.tsx` provides the minimum navigation shell: map surface
  placeholder, browser geolocation, destination search/selection, route
  mode selection, loading/error states, and normalized route result rendering.
- Destination search is implemented through the provider-neutral geocoding
  client and selected coordinates are passed to the existing route client.
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

## Incident UI

- `frontend/lib/incidents.ts` contains typed incident enums, public response
  validation, list filters, report submission, and incident detail API calls.
- `frontend/components/incidents/incident-panel.tsx` provides the community
  report form, validation and submission states, category/severity/status/
  confidence/time filters, incident list, and detail view.
- `frontend/app/page.tsx` mounts the incident panel without changing route
  comparison or heatmap behavior. Exact coordinates are used only for the
  existing API contract; displayed locations are rounded to approximate
  coordinates and reporter identity is never requested or shown.

## End-to-End Integration

- `frontend/app/page.tsx` keeps location, destination selection, route mode,
  route loading/error state, selected-route summary, heatmap state, and the
  incident panel in one demo flow.
- Changing FASTEST, BALANCED, or SAFETY_PRIORITY after a destination and
  current location are selected requests a fresh comparison from
  `POST /api/v1/routes`; the frontend does not calculate costs or risk.
- Destination changes clear stale route results. Route loading disables mode
  and destination controls to avoid contradictory results.
- Heatmap and incident errors remain isolated from route errors, so one
  unavailable service does not hide the other contextual UI.
- After a successful community report, the incident panel can refresh an
  active route comparison through the existing route API. The frontend does
  not calculate or cache safety values.

## Destination Search

- `backend/app/providers/routing.py` now implements the existing
  `GeocodingProvider` protocol in `OpenRouteServiceProvider` using the
  server-side HeiGIT `/pelias/v1/search` endpoint and normalizes GeoJSON point
  results.
- `backend/app/services/geocoding.py` bounds normalized queries and result
  counts without knowing provider response details.
- `backend/app/api/routes/geocoding.py` exposes
  `GET /api/v1/geocoding/search` and maps configuration, timeout, rate-limit,
  HTTP, and malformed-response failures to stable API errors.
- The browser submits only search text and receives normalized labels and
  coordinates. `ROUTING_API_KEY` is never exposed to Next.js.

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
- `POST /api/v1/incidents/reports`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{incident_id}`
- `GET /api/v1/geocoding/search`

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

## T101 Integration Validation

`backend/tests/test_t101_integration.py` validates the internal route safety
pipeline with a deterministic provider stub and controlled incident records.
The test flow is:

`RouteRequest -> RoutingProvider -> normalized route candidates -> route
geometry -> IncidentService route-context contract -> IncidentSignalContext ->
SafetyEngine -> SafetyAssessment -> RouteComparisonService -> RouteResponse`

The fixture provides a shorter candidate with eight recent, higher-confidence
high-severity indicators and a longer candidate with one recent, unverified
low-severity indicator. An additional controlled incident is outside the
fixture corridor results and is not included in either assessment. The real
`IncidentService`, `SafetyEngine`, route comparison, and FastAPI route handler
are exercised; route geometry and the configured 100 metre corridor are
asserted at the repository boundary. FASTEST, BALANCED, and SAFETY_PRIORITY
are validated through the API, including selected-route consistency,
assessment propagation, contextual disclaimers, and the absence of incident
private fields in route responses. A geometry-less provider case verifies that
missing context remains explicit and is not treated as zero risk.

This environment has no usable Docker/PostGIS service, so the integration
tests do not execute the actual PostGIS query against a database. Existing
repository tests still compile the production corridor query and verify its
`ST_DWithin` and `ST_GeomFromText` operations. No live OpenRouteService request
was made because no valid API key is configured.

## T102 Community Reports Integration

`IncidentRepository.create` now commits a newly submitted report before the
request-scoped database session closes. This ensures a later request can see
the report through the normal repository path. The existing report remains
`unverified` with its existing confidence semantics.

The frontend passes a report-success callback from the navigation page into
the incident panel. If an active route exists, submission triggers a fresh
`POST /api/v1/routes` request using the selected mode and refreshes the
optional heatmap. If no route is active, the report remains available for the
next route request without changing the navigation flow.

`backend/tests/test_t102_integration.py` validates the report API, subsequent
incident retrieval, all three route modes, fresh corridor context, updated
SafetyEngine assessments, exclusion of an outside-corridor report, and route
response privacy. It also verifies the repository commit boundary with a
transaction-recording session. The test uses an in-process persistent fixture
and deterministic routing provider because live PostGIS and OpenRouteService
are unavailable; it does not claim live database or provider validation.

## Verification Performed

- `python3 -m pip install -e '.[test]' --user` from `backend/` — passed
- `python3 -m pytest -q` from repository root — passed, 94 tests
- `pytest -q tests/test_t101_integration.py` from `backend/` — passed, 5 tests
- `pytest -q tests/test_t102_integration.py` from `backend/` — passed, 2 tests
- `python3 -m pytest -q` after T102 changes — passed, 96 tests
- `python3 -m compileall backend` — passed
- `git diff --check` — passed
- `pnpm typecheck` from `frontend/` — passed
- `pnpm build` from `frontend/` — passed

Provider tests use mocked HTTP clients. No live map/routing provider
integration was run or claimed because no credential was configured.

## Known Limitations

- No live routing credential is configured in this environment.
- No live PostgreSQL/PostGIS integration verification was performed.
- No live map tiles or external geocoding/search request was performed.
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
- The incident UI has no frontend test framework in the current repository;
  type checking and the production build are the frontend verification.
- No live OpenRouteService/HeiGIT geocoding request was performed because no
  valid provider credential is configured.

## Exact Next Task

T104 — Emergency integration, or complete T052 Safe Trip start if the Safe
Trip feature is continued before emergency work.

## T103 Handoff

T103 is complete for its documented scope. The backend now persists Safe Trip
plans as provider-neutral selected-route snapshots with a future expected
arrival and `planned` status. `POST /api/v1/trips` validates route geometry
endpoints and commits the plan through the repository boundary. The frontend
adds expected-arrival input and creation feedback to the selected-route panel.

Files added:

- `backend/app/models/trip.py`
- `backend/app/schemas/trip.py`
- `backend/app/repositories/trip.py`
- `backend/app/services/trips.py`
- `backend/app/api/routes/trips.py`
- `backend/alembic/versions/0002_create_safe_trips.py`
- `backend/tests/test_trips.py`
- `frontend/lib/trips.ts`

Files modified:

- backend model registration, dependencies, application router, and Alembic model imports
- `frontend/app/page.tsx`
- `docs/tasks.md`, `docs/api.md`, `docs/architecture.md`, and `docs/decisions.md`

The implementation deliberately does not start monitoring and does not add
location tracking, deviation detection, check-ins, completion, history,
trusted contacts, notifications, privacy controls, or SOS behavior.

Verification commands:

- `python3 -m pytest -q tests/test_trips.py` — passed, 4 tests
- `python3 -m pytest -q` — passed, 100 tests
- `pnpm typecheck` from `frontend/` — passed
- `pnpm build` from `frontend/` — passed
- `git diff --check` — passed
- `python3 -m compileall backend` — passed

Live PostgreSQL/PostGIS and OpenRouteService remain unavailable in this
environment; tests use in-process repositories and do not claim live
database/provider validation.
