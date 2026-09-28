# Nivara Agent Transfer

## Current Status

Foundation, incident domain, deterministic Safety Engine, and provider-neutral
navigation foundation are implemented. No concrete external map/routing
provider is configured yet.

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
- T014 Route normalization
- T015 Safety scoring
- T030 Incident model
- T031 Incident listing
- T032 Incident spatial queries
- T033 Community report creation
- T034 Community report validation
- T035 Confidence model
- T036 Incident filtering

T012 destination search, T013 concrete routing integration, T016 route
comparison, and T017–T020 route modes/heatmap remain incomplete.

## Navigation Architecture

Backend:

- `backend/app/schemas/routes.py` defines validated coordinates, route modes,
  provider-neutral geometry, route candidates, route responses, and future
  destination suggestions.
- `backend/app/providers/routing.py` defines `RoutingProvider` and
  `GeocodingProvider` protocols, normalized `ProviderRoute`, and explicit
  provider error types.
- `backend/app/services/routes.py` calls a provider and normalizes results into
  Nivara-owned `RouteResponse` objects.
- `backend/app/api/routes/routes.py` exposes `POST /api/v1/routes` and maps
  provider failures to `503` without leaking implementation details.
- `UnconfiguredRoutingProvider` is the current development default. It fails
  explicitly; it does not fabricate routes.

Frontend:

- `frontend/lib/navigation.ts` defines the frontend route contract and API
  client without exposing map credentials.
- `frontend/app/page.tsx` provides the minimum navigation shell: map surface
  placeholder, browser geolocation, coordinate-based destination input, route
  mode selection, loading/error states, and normalized route result rendering.
- Destination search is intentionally not implemented until a geocoding
  provider adapter is selected.

## Safety Integration Boundary

The route contract includes an optional `safety_assessment` field so future
navigation work can enrich normalized candidates with the existing
`IncidentSignalContext -> SafetyEngine -> SafetyAssessment` flow. T010 does not
collect incidents, invoke the Safety Engine, compare routes, or optimize modes.

The Safety Engine remains database-independent and is not called from route
handlers.

## API

Implemented:

- `POST /api/v1/routes`

The request accepts origin, destination, and `fastest`, `balanced`, or
`safety_priority` mode. The response contains normalized route candidates. If
the routing provider is not configured, the endpoint returns `503` with
`routing_provider_unavailable`.

No route data is mocked in the application path.

## Verification Performed

- `python3 -m pip install -e '.[test]' --user` from `backend/` — passed
- `pytest -q` from `backend/` — passed, 34 tests
- `python3 -m compileall -q app` — passed
- `git diff --check` — passed
- `pnpm typecheck` from `frontend/` — passed
- `pnpm build` from `frontend/` — passed

Backend provider tests use an in-process fake provider. No live map/routing
provider integration was run or claimed.

## Environment Variables

`MAP_API_KEY` already exists in `.env.example` for a future selected adapter.
It is not exposed to the frontend and is not used by the unconfigured provider.
No additional provider-specific variables were added.

## Known Limitations

- No concrete map/routing provider adapter is selected or configured.
- No live map tiles or external geocoding/search.
- Destination entry currently accepts latitude/longitude rather than place
  search.
- Route modes are validated and carried through the contract but do not yet
  implement fastest/balanced/safety-priority optimization.
- Route candidates are not yet enriched with incident-derived assessments.
- The map surface is a frontend shell, not a custom map engine.

## Exact Next Task

T013 — Select and implement one concrete external routing provider adapter,
including provider response normalization and a safe development configuration.
Then a later agent can implement route comparison and Safety Engine enrichment.
