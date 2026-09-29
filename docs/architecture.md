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
    +-- Safe Places
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

Safe Places currently uses a small deterministic, provider-neutral demo catalog
and haversine distance ordering so the MVP works without fabricating live place
data. Privacy settings are an in-process prototype boundary until authentication
and durable user settings exist.

Emergency orchestration reuses the active Safe Trip and latest-location
repositories. Its notification boundary is a mock provider only. Privacy flags
are consulted before reporting sharing status, but there is no authenticated
user/contact delivery integration yet.

## Data retention and sensitive logging

The current system stores incident reports, Safe Trip lifecycle/location/check-in
records, trusted contacts, sharing preferences, and emergency lifecycle records
through the existing database models. It does not implement automatic expiry or
user-requested deletion workflows. Production work must add authenticated
ownership, explicit retention periods, deletion/expiry jobs, and audit-safe
privacy handling. Backend code contains no intentional logging of coordinates,
contact values, emergency payloads, credentials, tokens, or passwords; the demo
seed script prints only an aggregate count.

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

Safe Trip check-ins are persisted separately from the trip row through the
`SafeTripCheckInService` and `SafeTripCheckInRepository`. The service permits
only explicit check-ins for active trips and assigns the timezone-aware server
timestamp; it does not infer status, store location, or trigger escalation.
Completion is a separate explicit service transition from `active` to
`completed`; it assigns a server-generated timezone-aware timestamp and does
not infer arrival from location, deviation, expected arrival, or check-ins.
History is derived read-only from the existing Safe Trip lifecycle row through
`SafeTripRepository.list_history` and a focused service/schema projection; it
does not create redundant lifecycle events or return tracking/check-in data.

### Emergency

SOS and emergency state management.

### Trusted Contacts

User-configured emergency contacts.

The current foundation stores provider-neutral phone or email contacts through
dedicated model, repository, service, and API layers. DELETE deactivates a
contact without invoking notification delivery. No user ownership relation is
currently enforceable because authentication is not implemented.

The contact list repository returns active contacts only, ordered by creation
time and ID for deterministic results, with a bounded 100-item prototype
response. The list projection contains only contact-management fields and no
Safe Trip, location, emergency, or provider metadata.

Contact updates are partial service-layer transitions that validate the
resulting contact method/value pair and preserve the contact ID. DELETE is
soft deactivation, so existing Safe Trip associations and sharing preferences
remain attached to the historical contact row.

Sharing permissions use a separate one-to-one
`trusted_contact_sharing_preferences` model. The three explicit permissions
(`allow_trip_status`, `allow_location`, and `allow_emergency`) default to false.
GET lazily initializes a restrictive row for active contacts; PATCH updates
only supplied fields. Preferences configure future workflows and do not invoke
delivery or emergency behavior.

Safe Trip selections use a separate `safe_trip_trusted_contacts` association
model and repository with a composite key over trip/contact IDs. Planned and
active trips may select multiple active contacts; completed trips are read-only.
The association stores no duplicated phone/email value and has no notification
side effects. Removing an association leaves the Trusted Contact intact.

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

The frontend integration keeps the selected destination coordinate as the
single handoff between geocoding and routing. Mode changes re-request the
backend route comparison when location and destination are available. Route
results, heatmap indicators, and incident browsing remain separate API-backed
views; the frontend does not calculate safety scores or route costs.

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

The frontend renders the returned points as contextual cells on the Leaflet map.
This is a visualization layer, not a map engine or a route-selection algorithm.
No-data cells are omitted and are not assigned a low-risk score.

The navigation page uses a client-only `frontend/components/map/nivara-map.tsx`
component. It renders OpenStreetMap-compatible development tiles, backend
route geometries, current-location and destination markers, and heatmap cells.
Leaflet is loaded only in the browser; route requests and provider credentials
remain behind the Nivara API.

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

T103 stores the selected route as a provider-neutral snapshot with a future
expected arrival and `planned` status. T052 adds the first lifecycle
transition: `planned -> active`, with a server-generated timezone-aware
`started_at` timestamp. The route snapshot and expected arrival are immutable
through this transition. T053 stores each active-trip location update in the
separate `safe_trip_locations` PostGIS-backed table. It preserves the device
`recorded_at` and server `received_at` timestamps and does not calculate route
deviation, safety, or trip state. T054 evaluates the latest stored location
against the Safe Trip snapshot's planned LineString using PostGIS geography
distance in metres and a configurable corridor threshold. It returns a
current-location assessment only; it does not persist deviation state or
implement hysteresis. T055 owns user-facing deviation feedback. Location
history retrieval, check-ins, completion, and history remain later tasks.

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

## 16. Synthetic demo data

Development demonstrations may use the explicit
`backend/scripts/seed_demo_data.py` utility. It writes only stable,
`[DEMO]`-marked synthetic Incident records through the existing model and
PostGIS geometry conventions. The seed is not run at application startup,
does not alter the SafetyEngine or route comparison, and never deletes
unrelated incident records.

## 17. Emergency workflow

Emergency records are independent lifecycle entities with optional Safe Trip
association. The service owns the state machine `active -> acknowledged ->
resolved`, with direct `active -> resolved` also allowed. Trip-linked SOS uses
only the latest explicitly recorded location and does not start background
GPS.

Notification delivery is isolated behind `EmergencyNotificationProvider`. The
current implementation is a mock/demo provider and records only minimal IDs in
memory; it sends no real messages. Resource discovery returns deterministic
placeholders. No emergency-service dispatch or response guarantee is implied.
