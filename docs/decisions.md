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
