# Nivara Architecture

## 1. Overview

Nivara is a contextual safety-aware navigation and journey protection platform.

The architecture separates:

- presentation
- API
- business logic
- persistence
- external integrations
- AI processing

The safety intelligence layer is the primary differentiating component.

---

## 2. Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

### Backend

- FastAPI
- Python

### Database

- PostgreSQL
- PostGIS

### External services

- map/routing provider
- geocoding/places provider where required
- AI provider
- notification provider where available

---

## 3. High-Level Architecture

Next.js
    |
    | HTTPS / REST
    v
FastAPI
    |
    +------------------------------+
    |                              |
    v                              v
Services                       Integrations
    |                              |
    +-- Safety Engine              +-- Maps
    +-- Routing                    +-- Geocoding
    +-- Incidents                  +-- Places
    +-- Community Reports          +-- AI
    +-- Safe Trip                  +-- Notifications
    +-- Emergency
    +-- Trusted Contacts
    +-- Privacy
    |
    v
Repositories
    |
    v
PostgreSQL + PostGIS

The runnable foundation is split into `backend/app/api`, `services`,
`repositories`, `models`, and `db`. `backend/app/db/session.py` owns the
SQLAlchemy async engine/session boundary; feature agents should inject the
session into repositories rather than opening connections in route handlers.

The frontend foundation uses the Next.js App Router. Shared UI primitives live
under `frontend/components/ui`, API configuration under `frontend/lib`, and
feature UI should be added without placing domain logic in `app/page.tsx`.

---

## 4. Backend Layering

API
 ->
Service
 ->
Repository
 ->
Database

### API

Responsible for:

- HTTP
- request validation
- authentication
- authorization
- response serialization

### Service

Responsible for:

- business logic
- orchestration
- safety scoring
- trip state transitions
- emergency workflows

### Repository

Responsible for:

- database operations
- spatial queries
- persistence

---

## 5. Safety Engine

The safety engine combines contextual signals.

Conceptual formula:

routeCost =
    timeWeight * travelTime
    +
    safetyWeight * safetyRisk
    +
    isolationWeight * isolationRisk

Possible signals:

- incident density
- incident recency
- incident severity
- community report confidence
- time of day
- lighting
- activity
- open businesses
- emergency resources
- route isolation

The weights must be configurable.

The score is an estimate, not a guarantee.

---

## 6. Route Modes

### Fastest

Optimize primarily for travel time.

### Balanced

Balance travel time and contextual safety indicators.

### Safety Priority

Increase the weight of safety indicators while maintaining reasonable travel time.

---

## 7. Geospatial Data

PostGIS should support:

- incident points
- route geometry
- proximity searches
- heatmap aggregation
- nearby resources
- spatial filtering

Avoid unnecessary custom spatial algorithms when PostGIS can perform the operation.

---

## 8. Core Domains

### Routing

External route acquisition and route normalization.

### Safety

Contextual scoring and explanations.

### Incidents

Structured incident records.

### Community Reports

User-submitted reports and confidence handling.

### Safe Trip

Journey lifecycle and monitoring.

### Emergency

SOS and emergency state management.

### Trusted Contacts

User-configured emergency contacts.

### Safe Places

Nearby assistance/resource discovery.

### Privacy

Location-sharing and data-retention controls.

### AI

Unstructured incident classification and extraction.

---

## 9. Data Flow

User
 ->
Frontend
 ->
FastAPI
 ->
Relevant service
 ->
Repository / integration
 ->
Database / external service
 ->
Service
 ->
API
 ->
Frontend

---

## 10. Navigation Data Flow

Current location
    ->
Destination
    ->
Routing provider
    ->
    Candidate routes
    ->
Incident corridor context
    ->
    Safety engine
    ->
Route comparison
    ->
Fastest / Balanced / Safety Priority
    ->
User

Destination search follows a separate provider-neutral boundary:

Frontend
    ->
`GET /api/v1/geocoding/search`
    ->
GeocodingService
    ->
GeocodingProvider
    ->
OpenRouteService geocoding API

The service returns normalized `DestinationSuggestion` objects. Provider
credentials and response formats do not reach the browser. Route calculation
continues to receive only the selected normalized coordinate.

The navigation foundation keeps external routing behind
`backend/app/providers/routing.py`. `RoutingService` consumes the provider
protocol and returns normalized Nivara route contracts. Provider-specific
response formats do not cross into API or frontend code. A concrete provider
adapter is implemented for openrouteservice's Directions GeoJSON API, while
the protocol remains replaceable.

`RoutingService` optionally coordinates `IncidentService`, the database-
independent `IncidentSignalContext`, `SafetyEngine`, and
`RouteComparisonService`. Incident corridor collection remains in the
repository layer and uses PostGIS `ST_DWithin` against a route LineString.
The configured corridor width is `ROUTE_CORRIDOR_RADIUS_METERS` (100 metres by
default, bounded to 25–1000 metres). Safety scoring is not performed in API
handlers or provider adapters.

Route comparison currently uses only travel time and incident-derived risk;
isolation and other future signals are intentionally absent until supported by
their own contracts. Mode weights are centralized: FASTEST 0.90/0.10,
BALANCED 0.55/0.45, and SAFETY_PRIORITY 0.25/0.75 for time/safety.

---

## 11. Safety Heatmap Data Flow

Map viewport
    ->
Bounded PostGIS incident query
    ->
Deterministic coarse grid aggregation
    ->
IncidentSignalContext per occupied cell
    ->
SafetyEngine
    ->
Contextual heatmap points

`GET /api/v1/safety/heatmap` accepts a bounded viewport and a small grid
dimension. The incident repository performs the `ST_MakeEnvelope` and
`ST_Intersects` query; the service assigns returned incidents to cells and
passes each occupied cell's signals to the existing database-independent
SafetyEngine. The API exposes cell centers, assessment values, and aggregate
counts only. It omits raw incident identity and other unnecessary details.

The frontend currently renders the returned points as a lightweight CSS
contextual overlay on the existing map shell. This is a visualization layer,
not a map engine or a route-selection algorithm. No-data cells are omitted and
are not assigned a low-risk score.

---

## 12. Safe Trip Data Flow

Selected route
    ->
Safe Trip creation
    ->
Expected arrival
    ->
Location updates
    ->
Deviation analysis
    ->
Check-in / assistance
    ->
Trip completion

---

## 13. Emergency Data Flow

SOS activation
    ->
Emergency event
    ->
Current location
    ->
Configured contacts
    ->
Emergency resources
    ->
Location sharing
    ->
Resolution

---

## 14. Privacy

Location is sensitive.

The system should minimize:

- collection
- retention
- logging
- unnecessary sharing

Location sharing must be controlled by explicit user settings.

---

## 15. Future News Pipeline

News
 ->
Extraction
 ->
Classification
 ->
Location extraction
 ->
Geocoding
 ->
Incident record
 ->
Safety engine

This pipeline is independent from the core product.
