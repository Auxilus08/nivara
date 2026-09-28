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
Safety engine
    ->
Route comparison
    ->
Fastest / Balanced / Safety Priority
    ->
User

---

## 11. Safe Trip Data Flow

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

## 12. Emergency Data Flow

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

## 13. Privacy

Location is sensitive.

The system should minimize:

- collection
- retention
- logging
- unnecessary sharing

Location sharing must be controlled by explicit user settings.

---

## 14. Future News Pipeline

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
