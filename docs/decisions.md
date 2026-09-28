# Nivara Architectural Decisions

## ADR-001: Frontend

Decision:

Use Next.js + TypeScript + Tailwind CSS + shadcn/ui.

Reason:

Fast development and strong component ecosystem.

---

## ADR-002: Backend

Decision:

Use FastAPI + Python.

Reason:

Fast API development, automatic OpenAPI generation, and strong AI/geospatial ecosystem.

---

## ADR-003: Database

Decision:

Use PostgreSQL + PostGIS.

Reason:

Nivara requires geospatial operations such as:

- proximity queries
- incident regions
- route analysis
- heatmaps
- nearby resources

---

## ADR-004: External Maps

Decision:

Use an external mapping/routing provider.

Reason:

Nivara's differentiating technology is safety intelligence, not map rendering or route graph construction.

---

## ADR-005: Contextual Safety Language

Decision:

Never claim a location is objectively safe or dangerous.

Reason:

Safety indicators are contextual estimates based on available information.

---

## ADR-006: News Ingestion

Decision:

News ingestion remains independent from the core application.

Reason:

The core product must function without web/news scraping.

---

## ADR-007: AI

Decision:

Use AI primarily for unstructured information processing.

Examples:

- incident classification
- severity extraction
- location extraction
- future news processing

AI must not replace deterministic security or authorization logic.

---

## ADR-008: Privacy

Decision:

Treat location as sensitive data.

Reason:

Precise location can expose a user's movement and routines.

---

## ADR-009: Multi-Agent Architecture

Decision:

Use repository documentation and task tracking as the shared source of truth.

Reason:

Multiple agents cannot depend on chat history to understand implementation state.

---

## ADR-010: Task Ownership

Decision:

Agents should work on scoped tasks and avoid unrelated changes.

Reason:

Reduces merge conflicts and architectural drift.

---

## ADR-011: Runnable foundation boundaries

Decision:

Use a small FastAPI application factory with versioned routers, Pydantic
settings, SQLAlchemy async session wiring, and a Next.js App Router shell.
Expose both `/api/v1/health` for clients and `/health` for infrastructure
probes.

Reason:

This keeps feature agents independent at the API/service/repository boundaries
while allowing the application and frontend to run before feature integrations
or a local database are available.

---

## ADR-012: Incident confidence and safety input boundary

Decision:

Persist incident context in PostGIS-backed repositories and expose a
database-independent incident signal DTO from the incident service. Confidence
uses explainable levels (`unverified`, `corroborated`, `higher_confidence`) and
factors rather than a probability score.

Reason:

The Safety Engine must consume contextual incident indicators without knowing
SQL or PostGIS details, and a single community report must not be presented as
validated truth.

---

## ADR-013: Deterministic incident-derived safety assessment

Decision:

Implement safety assessment as a pure service that consumes
`IncidentSignalContext` and returns an explainable 0–100 contextual estimate.
The centralized weights are incident density 35, recency 25, severity 25,
confidence 10, and category activity 5. Risk levels are LOW (0–24), MODERATE
(25–49), ELEVATED (50–74), and HIGH (75–100).

Reason:

Future routing consumers need a stable, database-independent safety input. A
small deterministic model is inspectable and testable for the hackathon while
avoiding unsupported probability claims or premature machine learning.

---

## ADR-014: Provider-neutral navigation boundary

Decision:

Keep routing and geocoding behind provider protocols and normalize route data
before it reaches the API or frontend. Until a concrete external provider is
selected and configured, the route API returns an explicit unavailable error
rather than fabricated route results.

Reason:

Nivara should depend on external routing capability without coupling its core
contracts to an unselected vendor or exposing provider credentials to the
browser.

---

## ADR-015: Initial external routing provider

Decision:

Use openrouteservice's Directions GeoJSON API as the first concrete routing
adapter. The adapter sends POST requests to
`https://api.openrouteservice.org/v2/directions/driving-car/geojson` with the
server-side `Authorization` API key and normalizes GeoJSON `LineString`
coordinates plus summary distance and duration into `ProviderRoute`.

Reason:

Its documented HTTP API accepts coordinate pairs and returns route geometry,
distance, and duration suitable for the current contract. The adapter remains
behind `RoutingProvider` so it can be replaced without changing API, frontend,
incident, or Safety Engine code. Route modes are passed through as contract
values only; this adapter does not claim safety-aware optimization.

---

## ADR-016: Route comparison and incident corridor enrichment

Decision:

Keep route comparison in a provider-neutral service. `RoutingService` obtains
route-corridor incident context through `IncidentService`, passes the resulting
`IncidentSignalContext` to the existing `SafetyEngine`, and attaches each
available `SafetyAssessment` before comparison. The repository uses a PostGIS
LineString corridor query with a configurable 100-metre default.

Comparison normalizes each candidate's duration against the slowest candidate
and combines it with the 0–100 contextual risk score. The time/safety weights
are FASTEST 0.90/0.10, BALANCED 0.55/0.45, and SAFETY_PRIORITY 0.25/0.75.
When any candidate lacks incident context, all candidates are compared by
normalized travel time only and the response explains that limitation; missing
context is never represented as low risk.

Reason:

This creates the first route-selection vertical slice without changing the
deterministic SafetyEngine or coupling it to SQL/PostGIS/provider formats.
The result remains an estimate based on available data and is not a guarantee
of safety.

---

## ADR-017: FASTEST mode semantics

Decision:

Define FASTEST as the route-selection objective with time weight `0.90` and
safety weight `0.10`. It uses the same normalized travel-time and contextual
risk formula as the other modes, so available `SafetyAssessment` data remains
visible even when travel time dominates selection.

For equal comparison costs, selection is deterministic: lower estimated
duration wins, then lexicographically lower `route_id`. FASTEST describes the
configured objective; it does not claim an objectively fastest, shortest, or
safe route.

Reason:

Users need a clear travel-time-oriented mode without losing contextual safety
information or introducing nondeterministic route selection.

---

## ADR-018: BALANCED mode semantics

Decision:

Define BALANCED as the route-selection objective with time weight `0.55` and
safety weight `0.45`. It uses the existing normalized travel-time score and
the existing SafetyEngine risk score without introducing a second safety
model. A faster route can lose when its risk score is sufficiently higher; a
lower-risk route can lose when its travel-time penalty is sufficiently large.

Reason:

The mode must express a genuine trade-off between travel efficiency and
available contextual incident indicators while preserving provider-neutral
contracts and deterministic comparison behavior.

---

## ADR-019: SAFETY_PRIORITY mode semantics

Decision:

Define SAFETY_PRIORITY as the route-selection objective with time weight `0.25`
and safety weight `0.75`. It uses the existing normalized travel-time score and
the existing SafetyEngine risk score. A slower route with materially lower
estimated risk can be selected, but a sufficiently large travel-time penalty
can still outweigh lower risk.

Reason:

The mode should prioritize lower estimated incident risk without presenting any
route as safe or guaranteed to protect the user. Keeping a non-zero time weight
prevents the mode from becoming a simple longest-route selector.

---

## ADR-020: Bounded contextual safety heatmap

Decision:

Expose `GET /api/v1/safety/heatmap` as a bounded viewport query. The repository
uses PostGIS `ST_MakeEnvelope` and `ST_Intersects` to retrieve incidents within
the requested bounds. The service assigns incidents to a deterministic coarse
grid, builds an `IncidentSignalContext` for each occupied cell, and calls the
existing SafetyEngine to produce the cell's assessment. It returns cell centers
and aggregate contextual fields only; empty cells are omitted rather than
being treated as lower risk.

The viewport is limited to a 0.02–2 degree span, grid dimensions to 2–12 per
axis, and repository results to a bounded maximum. This provides a practical
visualization while limiting database work and reducing unnecessary exposure of
precise incident locations. The frontend uses a dependency-free CSS overlay on
the current map shell until a concrete map-rendering provider is selected.

Reason:

The heatmap must reuse the canonical deterministic SafetyEngine without
introducing a second frontend score or a database dependency in that engine.
Coarse aggregation provides contextual indicators for the hackathon UI while
preserving non-guaranteed safety language and avoiding reporter or raw incident
data exposure.

---

## ADR-021: Server-side destination geocoding

Decision:

Use the existing `GeocodingProvider` abstraction and the current
OpenRouteService/HeiGIT forward geocoding endpoint at `/pelias/v1/search`.
Expose it through
`GET /api/v1/geocoding/search`, validate and bound the query in the API layer,
and normalize responses into Nivara-owned `DestinationSuggestion` objects.
The existing server-side `ROUTING_API_KEY` is sent only from the backend.

Reason:

Destination search is an external integration and must not couple the frontend
to provider payloads or expose credentials. A bounded explicit search action is
sufficient for the current navigation shell without adding autocomplete
traffic or a second geocoding abstraction.

---

## ADR-022: Backend-owned integration orchestration

Decision:

Keep the end-to-end demo orchestration in the existing frontend shell while
delegating destination resolution, route acquisition, incident corridor
collection, SafetyEngine assessment, and route comparison to their existing
backend boundaries. Changing a selected route mode requests a new backend
comparison; no route cost or safety score is calculated in TypeScript.

Reason:

This connects the completed vertical slices for demonstration without creating
a second safety model or coupling the browser to providers. Independent
heatmap and incident-panel failures remain visible without preventing route
requests.
