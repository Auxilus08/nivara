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
