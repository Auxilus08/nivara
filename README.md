# Nivara

> Contextual safety-aware navigation and journey protection for safer everyday travel.

Nivara is a safety intelligence layer built on top of conventional navigation. It combines route information, contextual incident indicators, community reports, geospatial analysis, and journey-protection workflows to help users make more informed travel decisions.

Nivara is designed around a simple principle: navigation should consider more than distance and travel time. The system provides contextual indicators and explanations rather than claiming that any route or location is objectively safe or dangerous.

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [How Nivara Works](#how-nivara-works)
- [Navigation Modes](#navigation-modes)
- [Safety Intelligence](#safety-intelligence)
- [Community Incident Reporting](#community-incident-reporting)
- [Safe Trip](#safe-trip)
- [Emergency Assistance](#emergency-assistance)
- [Trusted Contacts](#trusted-contacts)
- [Safe Places](#safe-places)
- [Privacy](#privacy)
- [AI Layer](#ai-layer)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [API Surface](#api-surface)
- [Safety and Privacy Principles](#safety-and-privacy-principles)
- [Current Implementation Status](#current-implementation-status)
- [Local Development](#local-development)
- [Testing](#testing)
- [Environment Configuration](#environment-configuration)
- [Development Principles](#development-principles)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Overview

Traditional navigation systems primarily optimize for factors such as distance and estimated travel time. Nivara adds a contextual safety layer that evaluates available signals around candidate routes and presents the result as explainable safety indicators.

The core navigation experience supports three route modes:

- **Fastest** — prioritizes travel time while retaining available safety indicators.
- **Balanced** — balances travel time with contextual safety indicators.
- **Safety Priority** — gives greater weight to available safety indicators while retaining reasonable travel time.

The same route can have different contextual indicators at different times because incident activity and other signals can change.

Nivara does not replace emergency services and does not guarantee personal safety.

## Core Features

### Navigation

- Browser-based current-location acquisition.
- Destination search through a provider-backed geocoding service.
- External routing provider integration.
- Provider-neutral routing abstraction.
- Normalized route candidates and route geometry.
- Alternative route comparison.
- Three route-selection modes: Fastest, Balanced, and Safety Priority.
- Route duration, distance, geometry, and comparison information.
- Contextual safety assessment attached to route candidates.
- Route recalculation after relevant community reports are submitted.

### Contextual Safety Intelligence

- Deterministic, explainable Safety Engine.
- Incident-density signals.
- Recent incident activity.
- Incident severity weighting.
- Community-report confidence weighting.
- Contextual risk score from 0–100.
- Risk levels: LOW, MODERATE, ELEVATED, and HIGH.
- Assessment confidence levels.
- Human-readable contributing factors.
- Safety-aware route comparison.
- Coarse safety heatmap for map visualization.
- Explicit handling for missing safety context; unavailable data is not treated as zero risk.

The current implemented Safety Engine is intentionally deterministic and database-independent. Future signals can include time of day, lighting, activity, open businesses, emergency-resource accessibility, and route isolation.

### Community Incident Reporting

Users can submit structured community reports with controlled categories and severity levels, descriptions, location, and optional occurrence timestamps.

The incident system supports:

- Incident creation.
- Incident retrieval.
- Spatial and bounded-radius queries.
- Category, severity, status, confidence, and time filtering.
- Deterministic contextual confidence handling.
- Privacy-preserving report responses.
- Approximate incident presentation in the frontend.
- Integration with subsequent route safety calculations.
- Automatic route/heatmap refresh after a successful report when relevant UI state is active.

Reporter identity is not collected by the current community-report workflow.

### Safe Trip

Safe Trip is the journey-protection layer built around a selected route. Its planned lifecycle includes:

```text
Selected Route
    -> Safe Trip Creation
    -> Expected Arrival
    -> Location Updates
    -> Deviation Analysis
    -> Check-in / Assistance
    -> Trip Completion
```

The Safe Trip domain is being implemented incrementally, with creation, monitoring, deviation detection, check-ins, completion, and history separated into individual development tasks.

### Trusted Contacts

The planned trusted-contact system supports:

- Creating trusted contacts.
- Listing contacts.
- Updating contacts.
- Removing contacts.
- Configuring sharing preferences.

Trusted contacts are intended to integrate with Safe Trip and emergency workflows without exposing unnecessary location information.

### Emergency Assistance

The emergency domain is designed around an explicit emergency-event lifecycle:

```text
SOS Activation
    -> Emergency Event
    -> Current Location
    -> Configured Contacts
    -> Emergency Resources
    -> Location Sharing
    -> Resolution
```

Planned capabilities include:

- SOS activation.
- Emergency event state management.
- Contact-notification abstraction.
- Nearby emergency-resource discovery.
- Emergency acknowledgement.
- Emergency resolution.
- Privacy-aware location sharing.

### Safe Places

Nivara is designed to help users discover nearby assistance resources, including potential categories such as:

- Hospitals.
- Police stations.
- Petrol pumps.
- Hotels.
- Open businesses.
- Other relevant assistance locations.

The intended workflow is discovery, filtering/ranking, and navigation to the selected resource.

### Privacy Controls

Location is treated as sensitive data throughout the architecture.

The privacy layer is designed to control:

- Location sharing.
- Trusted-contact sharing.
- Emergency sharing.
- Data retention.
- Sensitive logging.

The system follows data-minimization principles: collect, retain, log, and share only what is required for the relevant workflow.

### AI-Assisted Processing

AI is intentionally not placed in the critical route-selection loop.

The planned AI layer is intended for unstructured information processing, such as:

- Incident classification.
- Structured incident extraction.
- Future news processing.
- Location extraction and normalization from unstructured sources.

The core routing and Safety Engine remain deterministic and explainable.

## How Nivara Works

At a high level:

```text
User
  |
  v
Next.js Frontend
  |
  | HTTPS / REST
  v
FastAPI API
  |
  +-----------------------------+
  |                             |
  v                             v
Services                    External Integrations
  |                             |
  +-- Routing                   +-- Routing / Geocoding
  +-- Safety                    +-- Places
  +-- Incidents                 +-- AI
  +-- Safe Trip                 +-- Notifications
  +-- Emergency
  +-- Trusted Contacts
  +-- Privacy
  |
  v
Repositories
  |
  v
PostgreSQL + PostGIS
```

### Navigation Data Flow

```text
Current Location
      |
      v
Destination Search
      |
      v
Routing Provider
      |
      v
Normalized Candidate Routes
      |
      v
Route Geometry / Corridor
      |
      v
Incident Context
      |
      v
IncidentSignalContext
      |
      v
SafetyEngine
      |
      v
SafetyAssessment
      |
      v
RouteComparisonService
      |
      +---- Fastest
      +---- Balanced
      +---- Safety Priority
      |
      v
Route Response
      |
      v
Frontend
```

### Community Report → Navigation Flow

```text
Community Report
      |
      v
POST /api/v1/incidents/reports
      |
      v
Incident Persistence
      |
      v
Later Route Request
      |
      v
Fresh Route-Corridor Query
      |
      v
Incident Context
      |
      v
SafetyEngine
      |
      v
Updated SafetyAssessment
      |
      v
Route Comparison
```

This ensures that newly submitted reports can influence subsequent route assessments without placing scoring logic in the frontend.

## Navigation Modes

Nivara currently uses the following documented comparison model.

For candidate route `i`:

```text
normalized_travel_score
    = route_duration / maximum_candidate_duration * 100
```

The comparison cost is:

```text
comparison_cost
    = time_weight * normalized_travel_score
    + safety_weight * risk_score
```

Current weights:

| Mode | Travel Weight | Safety Weight |
|---|---:|---:|
| Fastest | 0.90 | 0.10 |
| Balanced | 0.55 | 0.45 |
| Safety Priority | 0.25 | 0.75 |

The current comparison model does not include an isolation score because that signal is not yet available in the implemented pipeline.

Tie-breaking is deterministic so that identical candidates produce stable selections.

## Safety Intelligence

The Safety Engine is intentionally separate from the database and routing provider.

Its current model uses:

| Signal | Maximum Contribution |
|---|---:|
| Incident density | 35 points |
| Recent incident activity | 25 points |
| Severity activity | 25 points |
| Confidence adjustment | 10 points |
| Category activity | 5 points |

Severity weighting currently follows:

```text
LOW       = 0.20
MEDIUM    = 0.60
HIGH      = 1.00
```

Confidence weighting currently follows:

```text
UNVERIFIED   = 0.25
CORROBORATED = 0.65
HIGHER       = 0.90
```

Risk levels are mapped to the resulting score:

```text
0–24    LOW
25–49   MODERATE
50–74   ELEVATED
75–100  HIGH
```

These values are contextual heuristics, not scientifically validated probabilities or guarantees of future events.

## Architecture

Nivara follows a layered backend architecture:

```text
API
  -> Service
      -> Repository / Provider
          -> Database / External Service
```

### API Layer

Responsible for:

- HTTP request handling.
- Input validation.
- Response serialization.
- Structured errors.
- Authentication/authorization boundaries as the relevant features are implemented.

### Service Layer

Responsible for:

- Business logic.
- Feature orchestration.
- Safety calculations.
- Route comparison.
- Trip state transitions.
- Emergency workflows.

### Repository Layer

Responsible for:

- Database operations.
- Spatial queries.
- Persistence.
- Data retrieval.

### Provider Layer

External services are hidden behind provider abstractions so the application is not tightly coupled to one routing/geocoding implementation.

### Safety Engine

The Safety Engine remains database-independent and consumes normalized contextual signal data.

## Technology Stack

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- shadcn-compatible UI components

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Database

- PostgreSQL
- PostGIS

### Routing / Geocoding

- OpenRouteService / HeiGIT provider integration
- Provider abstraction for future substitution

### Infrastructure / Development

- Docker Compose for local PostgreSQL/PostGIS where available
- pytest
- pnpm

## Project Structure

```text
nivara/
├── AGENTS.md
├── README.md
├── .env.example
├── docker-compose.yml
│
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── providers/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   └── pyproject.toml
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── decisions.md
│   ├── flow.md
│   ├── tasks.md
│   └── transfer.md
│
└── skills/
    ├── agent-handoff/
    ├── safety-engine/
    ├── security4her-backend/
    └── security4her-frontend/
```

## API Surface

The API is versioned under `/api/v1`.

### Health

```text
GET /health
GET /api/v1/health
```

### Navigation

```text
POST /api/v1/routes
GET  /api/v1/geocoding/search
```

### Safety

```text
GET /api/v1/safety/heatmap
```

### Incidents

```text
GET  /api/v1/incidents
POST /api/v1/incidents/reports
GET  /api/v1/incidents/{incident_id}
```

### Safe Trip

The planned Safe Trip API includes:

```text
POST /api/v1/trips
GET  /api/v1/trips/{trip_id}
POST /api/v1/trips/{trip_id}/start
POST /api/v1/trips/{trip_id}/check-in
POST /api/v1/trips/{trip_id}/complete
```

Additional Safe Trip endpoints will be introduced as their corresponding implementation tasks are completed.

### Trusted Contacts

Planned API surface:

```text
GET    /api/v1/trusted-contacts
POST   /api/v1/trusted-contacts
PATCH  /api/v1/trusted-contacts/{contact_id}
DELETE /api/v1/trusted-contacts/{contact_id}
```

### Emergency

Planned API surface:

```text
POST /api/v1/emergency/sos
GET  /api/v1/emergency/{event_id}
POST /api/v1/emergency/{event_id}/acknowledge
POST /api/v1/emergency/{event_id}/resolve
```

### Safe Places

```text
GET /api/v1/safe-places
```

### Privacy

```text
GET   /api/v1/privacy/settings
PATCH /api/v1/privacy/settings
```

> Endpoint availability follows the implementation status in `docs/tasks.md`. Planned endpoints are documented here for product context and are not presented as currently implemented unless their corresponding task is complete.

## Safety and Privacy Principles

### Contextual, not absolute

Nivara reports indicators and estimates. It does not determine whether a place or route is inherently safe or dangerous.

### Explainability

Safety assessments should expose meaningful contributing factors rather than producing unexplained scores.

### Data minimization

Collect only information required for the workflow.

### Privacy by design

Location data is sensitive. Avoid unnecessary collection, retention, logging, and sharing.

### No client-side safety scoring

The backend owns safety calculation and route comparison. The frontend renders the resulting context.

### No fabricated external data

External routing, geocoding, database, notification, and AI integrations must never be represented as live when they were only simulated or mocked in tests.

## Current Implementation Status

As of the current development state:

| Area | Status |
|---|---|
| Repository/foundation | Complete |
| FastAPI backend foundation | Complete |
| Next.js frontend foundation | Complete |
| PostgreSQL/PostGIS architecture | Complete |
| Routing abstraction | Complete |
| OpenRouteService integration | Complete |
| Destination/geocoding search | Complete |
| Current-location flow | Complete |
| Safety Engine | Complete |
| Fastest mode | Complete |
| Balanced mode | Complete |
| Safety Priority mode | Complete |
| Safety heatmap | Complete |
| Incident model and queries | Complete |
| Community reporting | Complete |
| Incident UI | Complete |
| Navigation end-to-end integration | Complete |
| Safety end-to-end integration validation | Complete |
| Community report → navigation integration | Complete |
| Safe Trip | Next implementation area |
| Trusted Contacts | Planned |
| Emergency workflow | Planned |
| Safe Places | Planned |
| Privacy controls | Planned |
| AI incident classification | Planned |
| News ingestion pipeline | Future |

T103 is the next planned task: Safe Trip model and creation flow.

## Local Development

### Prerequisites

Recommended tooling:

- Git
- Python 3
- Node.js
- pnpm
- Docker / Docker Compose for local PostgreSQL/PostGIS

### Clone

```bash
git clone https://github.com/Auxilus08/nivara.git
cd nivara
```

### Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Configure the required values for your environment. External routing/geocoding credentials should remain server-side and must never be committed.

### Backend

```bash
cd backend
python3 -m pip install -e '.[test]' --user
```

Run the backend using the project's normal FastAPI/uvicorn workflow.

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend uses the configured backend API URL from the environment.

### Database

Where Docker is available, the repository provides PostgreSQL/PostGIS configuration through Docker Compose.

The application should use Alembic migrations rather than manually modifying production database schemas.

## Testing

Backend test suite:

```bash
cd backend
python3 -m pytest -q
```

Compile check:

```bash
cd ~/projects/nivara
python3 -m compileall backend
```

Frontend type checking:

```bash
cd frontend
pnpm typecheck
```

Frontend production build:

```bash
pnpm build
```

Repository whitespace check:

```bash
git diff --check
```

The project distinguishes deterministic/in-process integration validation from live infrastructure validation. A passing test suite does not imply that a live OpenRouteService request or live PostGIS query was executed unless explicitly reported as such.

## Environment Configuration

The project uses environment-backed configuration. Important configuration areas include:

```text
APP_ENV
APP_DEBUG
CORS_ORIGINS
DATABASE_URL
ROUTING_PROVIDER
ROUTING_API_KEY
MAP_API_KEY
AI_API_KEY
NOTIFICATION_PROVIDER
NOTIFICATION_API_KEY
NEXT_PUBLIC_API_URL
ROUTE_CORRIDOR_RADIUS_METERS
```

Exact required values and defaults should be checked in `.env.example` and the backend configuration module.

Never commit real API keys, credentials, tokens, or private location data.

## Development Principles

1. Inspect before editing.
2. Preserve the existing architecture.
3. Prefer vertical, testable feature slices.
4. Keep business logic in services.
5. Keep persistence in repositories.
6. Keep external integrations behind provider abstractions.
7. Keep the Safety Engine deterministic and explainable.
8. Treat location as sensitive data.
9. Never fabricate external integrations or validation results.
10. Never present contextual safety estimates as guarantees.
11. Update relevant documentation after meaningful architectural changes.
12. Update `docs/tasks.md` and `docs/transfer.md` when completing a task.
13. Review `git diff` before finishing work.

## Roadmap

### Near term

- Safe Trip model and creation.
- Safe Trip start and lifecycle management.
- Location tracking.
- Route deviation detection.
- Deviation UI.
- Safety check-ins.
- Trip completion and history.

### Trusted contacts

- Contact model and CRUD.
- Sharing preferences.
- Integration with Safe Trip and emergency workflows.

### Emergency

- Emergency event model.
- SOS workflow.
- Emergency state machine.
- Notification abstraction.
- Emergency resources.
- Acknowledgement and resolution.

### Safe Places

- Nearby resource search.
- Resource filtering.
- Resource ranking.
- Navigation to resources.

### Privacy

- Privacy model.
- Location-sharing controls.
- Trusted-contact sharing controls.
- Emergency sharing controls.
- Data retention policy.
- Sensitive logging review.

### AI and future intelligence

- AI incident classification.
- Structured extraction.
- AI validation and failure handling.
- News ingestion.
- News extraction and geocoding.
- Advanced safety signals.

## Contributing

Contributions should follow the repository's engineering conventions.

Before opening a change:

1. Inspect the relevant architecture and task documentation.
2. Keep changes focused.
3. Add or update tests for meaningful behavior changes.
4. Run the relevant backend/frontend checks.
5. Run `git diff --check`.
6. Update documentation when API or architecture changes.
7. Do not commit secrets or sensitive location data.

For multi-agent development, `docs/transfer.md` and `docs/tasks.md` are the primary handoff mechanisms. The repository is the source of truth rather than conversation history.

## License

No project license has been specified in the current repository documentation. Add a license before distributing Nivara as an open-source project.