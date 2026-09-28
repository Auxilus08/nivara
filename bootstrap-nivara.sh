#!/usr/bin/env bash

set -euo pipefail

echo "=========================================="
echo "        Nivara Project Bootstrap"
echo "=========================================="
echo ""

PROJECT_ROOT="$(pwd)"

echo "[1/8] Creating project directories..."

mkdir -p \
    docs \
    skills/security4her-backend \
    skills/security4her-frontend \
    skills/safety-engine \
    skills/agent-handoff \
    frontend \
    backend \
    tests \
    scripts

echo "[2/8] Creating AGENTS.md..."

cat > AGENTS.md <<'EOF'
# Nivara - Agent Instructions

## 1. Mission

Build Nivara as a complete, coherent, hackathon-ready safety platform.

Nivara is a contextual safety-aware navigation and journey protection platform focused on:

- women's safety
- digital safety
- harassment prevention
- rapid access to help
- practical safety tools
- privacy-aware emergency workflows
- contextual safety intelligence

The goal is a working integrated product, not a collection of disconnected prototypes.

The repository is the source of truth.

Chat history is not the source of truth.

---

## 2. Product

Product name:

Nivara

Repository name:

nivara

Primary product concept:

A contextual safety intelligence layer on top of navigation.

Nivara should help users compare routes using both travel efficiency and contextual safety indicators.

Core capabilities:

- current location
- destination search
- fastest route
- balanced route
- safety-priority route
- route comparison
- contextual safety indicators
- safety heatmap
- community incident reporting
- incident history
- Safe Trip
- live journey monitoring
- route deviation detection
- safety check-ins
- trusted contacts
- SOS/emergency workflow
- nearby emergency resources
- nearby assistance/safe places
- privacy controls
- AI-assisted incident classification

---

## 3. Core Product Principle

Nivara must not claim that a location is objectively:

- safe
- dangerous
- guaranteed safe
- guaranteed dangerous

Use contextual language such as:

- lower estimated risk
- higher-risk indicators
- elevated incident activity
- limited activity detected
- better-lit route indicators
- more active area
- stronger emergency accessibility
- contextual safety indicators

Safety information is an estimate based on available data.

It is not a guarantee of what will happen.

---

## 4. Technology Stack

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

### Mapping

External map/routing provider.

Do not build a custom map engine.

Do not build a custom global routing graph.

### AI

Use AI where it provides meaningful value for unstructured information.

Examples:

- incident classification
- incident extraction
- severity classification
- future news processing

Do not use AI for deterministic operations that are better handled by normal code.

Examples:

- authorization
- database CRUD
- route geometry processing
- deterministic scoring
- state transitions
- validation

---

## 5. General Engineering Rules

1. Inspect before editing.
2. Understand existing code before changing it.
3. Preserve established architecture.
4. Do not independently redesign foundational architecture.
5. Prefer small, coherent changes.
6. Complete vertical slices where possible.
7. Keep interfaces explicit.
8. Keep business logic out of HTTP route handlers.
9. Validate all external input.
10. Never commit secrets.
11. Never hard-code API keys.
12. Treat location data as sensitive.
13. Do not expose private location data unnecessarily.
14. Do not fake external integrations.
15. Do not claim an integration works unless it actually works.
16. Write meaningful tests for important logic.
17. Handle loading, error and empty states in the frontend.
18. Keep API contracts documented.
19. Update relevant documentation after architectural changes.
20. Update tasks.md after completing work.
21. Update transfer.md before handing work to another agent.
22. Inspect git diff before finishing.
23. Do not claim tests passed unless they were actually executed.

---

## 6. Multi-Agent Development

Nivara will be developed using multiple Codex agents.

Agents must work within clearly defined scopes.

Possible feature areas:

- repository foundation
- frontend foundation
- backend foundation
- database foundation
- routing
- safety engine
- community reports
- Safe Trip
- route deviation
- check-ins
- trusted contacts
- emergency/SOS
- safe places
- privacy
- AI incident classification
- testing
- UI integration

Agents must not assume they own the entire repository.

Agents must not rewrite unrelated areas.

If a feature requires an architectural decision that affects multiple modules, document the decision instead of silently changing architecture.

---

## 7. Repository Structure

Expected high-level structure:

frontend/
backend/
tests/
docs/
skills/
scripts/

Important project documents:

docs/architecture.md
docs/flow.md
docs/api.md
docs/decisions.md
docs/tasks.md
docs/transfer.md

---

## 8. Backend Architecture

Prefer:

API
 ->
Service
 ->
Repository
 ->
Database

### API layer

Responsible for:

- HTTP routing
- request validation
- response serialization
- authentication dependencies
- authorization dependencies

### Service layer

Responsible for:

- business logic
- safety calculations
- trip state transitions
- emergency state transitions
- orchestration

### Repository layer

Responsible for:

- database access
- queries
- persistence

Do not place complex business logic directly in route handlers.

---

## 9. Frontend Architecture

Prefer separation between:

- pages/routes
- UI components
- feature components
- API clients
- hooks
- state
- types

Do not put large amounts of business logic directly inside presentation components.

Reusable UI should be preferred.

Use shadcn/ui where appropriate.

---

## 10. Safety Engine

Nivara's primary technical differentiator is contextual safety intelligence.

Conceptually:

routeCost =
    travelTimeWeight * travelTime
    +
    safetyWeight * safetyRisk
    +
    isolationWeight * isolationRisk

Potential signals:

- incident density
- incident recency
- incident severity
- time of day
- lighting indicators
- pedestrian/activity indicators
- open businesses
- emergency resource accessibility
- route isolation
- community reports
- corroboration/confidence
- proximity to assistance resources

The exact scoring implementation must remain configurable.

Do not present a heuristic score as a scientifically validated probability.

The UI must explain relevant contributing indicators where possible.

---

## 11. Routing Modes

Nivara should support:

### Fastest

Prioritize travel time.

### Balanced

Balance travel time with contextual safety indicators.

### Safety Priority

Give substantially greater weight to contextual safety indicators while maintaining reasonable travel time.

The safety-priority route must not simply mean "the longest route."

The system should optimize a multi-objective cost.

---

## 12. Community Reports

Supported report categories may include:

- harassment
- theft
- suspicious activity
- poor lighting
- unsafe/isolated area
- other

Reports should contain appropriate structured information such as:

- location
- category
- description
- timestamp
- severity where appropriate
- confidence/status
- source type

Do not allow a single unverified report to automatically dominate an area's safety calculation.

Use confidence/corroboration where appropriate.

---

## 13. Safe Trip

Safe Trip begins when the user chooses to protect a journey.

It may contain:

- selected route
- expected arrival time
- current position
- journey status
- deviation detection
- check-in
- trusted-contact sharing
- emergency escalation

A route deviation is not automatically an emergency.

The system should first ask the user whether they are okay when appropriate.

---

## 14. Route Deviation

When significant deviation is detected:

Show an appropriate prompt such as:

"You appear to have deviated from your planned route. Are you okay?"

Possible actions:

- I'm Safe
- Need Help

Do not automatically infer malicious intent.

Do not automatically classify every deviation as an emergency.

---

## 15. Safety Check-In

A user may define:

- expected arrival
- optional trusted contacts
- sharing preferences

If the expected arrival time passes without confirmation:

Ask the user to confirm their status.

Possible actions:

- I'm Safe
- Need Help

The exact behavior must respect privacy settings.

---

## 16. Trusted Contacts

Trusted contacts should support appropriate CRUD operations:

- create
- list
- update
- delete

Only share information according to the user's explicit configuration and emergency workflow.

---

## 17. SOS

SOS should use an intentional activation mechanism such as a hold-to-trigger interaction where appropriate.

Conceptual flow:

Hold SOS
 ->
Create emergency event
 ->
Capture current location
 ->
Notify configured trusted contacts according to consent
 ->
Show nearby emergency resources
 ->
Continue location sharing according to privacy settings
 ->
Resolve emergency

Suggested emergency states:

ACTIVE
ACKNOWLEDGED
RESOLVED

Do not claim that a real emergency service was contacted unless a real verified integration actually performed that action.

If a hackathon demo uses mocked notifications, clearly keep the mock behavior separate from production integrations.

---

## 18. Safe Places

Nivara may help users find nearby places/resources such as:

- hospitals
- police stations
- petrol pumps
- hotels
- open businesses
- other appropriate assistance locations

Ranking can consider:

- distance
- current/open status where available
- activity indicators
- emergency accessibility
- contextual safety signals

Do not describe any place as guaranteed safe.

---

## 19. Privacy

Location is sensitive information.

Privacy controls should be explicit.

Consider:

- whether live location is shared
- who receives it
- when sharing starts
- when sharing stops
- whether sharing continues during emergency
- data retention
- deletion
- consent

Never log precise location unnecessarily.

Avoid storing sensitive information in application logs.

---

## 20. AI

AI should primarily process unstructured information.

Example:

User report:

"Someone was following me near the bus stop and there were hardly any people around."

Possible structured output:

category:
suspicious_activity

environment:
low_activity

severity:
elevated

The AI output must be validated before being stored or used by deterministic systems.

Do not allow an LLM to directly perform privileged actions without deterministic validation.

---

## 21. Future News Pipeline

News ingestion is a future/independent capability.

Conceptual pipeline:

Article
 ->
Extraction
 ->
Incident classification
 ->
Location extraction
 ->
Date extraction
 ->
Severity/confidence
 ->
Geocoding
 ->
Incident database
 ->
Safety engine

The core application must not depend on news scraping.

Seeded structured incident data and community reports must be sufficient for the hackathon demo.

---

## 22. External Integrations

External integrations may include:

- mapping/routing
- geocoding
- places
- AI APIs
- notifications

Each integration should have a clear boundary.

Use environment variables for secrets.

Provide safe development fallbacks where appropriate.

Do not silently substitute fake production behavior for unavailable integrations.

---

## 23. Configuration

Use environment variables for:

- database URL
- map API keys
- AI API keys
- notification credentials
- other secrets

Never commit:

.env
.env.local
real credentials
private keys
tokens

Provide `.env.example` when environment variables become necessary.

---

## 24. API Versioning

API base path:

/api/v1

Keep API response structures consistent.

Use appropriate HTTP status codes.

Validate request bodies.

Return structured error responses.

---

## 25. Testing

Important areas requiring tests:

- safety scoring
- route comparison
- incident confidence
- trip state transitions
- route deviation
- check-in behavior
- emergency state transitions
- privacy behavior
- API validation
- critical frontend flows

Do not write tests merely to increase test count.

Test meaningful behavior.

---

## 26. Git Discipline

Prefer feature branches such as:

feature/safety-engine
feature/community-reports
feature/safe-trip
feature/emergency
feature/privacy
feature/ai-reports

Use focused commits.

Preferred commit prefixes:

feat:
fix:
docs:
refactor:
test:
chore:

Do not mix unrelated changes in one commit.

Before finishing:

git status
git diff

---

## 27. Documentation Rules

When architecture changes:

Update:

docs/architecture.md
docs/decisions.md

When API contracts change:

Update:

docs/api.md

When product flows change:

Update:

docs/flow.md

When task status changes:

Update:

docs/tasks.md

Before handing work to another agent:

Update:

docs/transfer.md

---

## 28. Definition of Done

A task is complete when:

- implementation exists
- relevant tests pass
- no obvious regression exists
- relevant documentation is updated
- tasks.md is updated
- transfer.md is updated
- git diff has been reviewed
- known issues are documented
- the next task is identified

---

## 29. Handoff Protocol

Before finishing:

1. Inspect git status.
2. Inspect git diff.
3. Run relevant tests.
4. Update docs/tasks.md.
5. Update docs/transfer.md.
6. Record known issues.
7. Record files changed.
8. Record commands used for verification.
9. Identify the exact next task.

The next agent should be able to continue without relying on chat history.

---

## 30. Scope Discipline

Do not:

- rewrite the architecture without justification
- add unnecessary technologies
- build a custom map engine
- build a custom routing engine
- add fake integrations
- expose secrets
- make unsupported safety claims
- make assumptions about user intent
- let AI replace deterministic security controls

When uncertain:

Inspect the repository.
Read the relevant documentation.
Preserve existing interfaces.
Document the decision.
EOF

echo "[3/8] Creating architecture documentation..."

cat > docs/architecture.md <<'EOF'
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
EOF

echo "[4/8] Creating product flow documentation..."

cat > docs/flow.md <<'EOF'
# Nivara Product Flows

## 1. Navigation

Current location
    ->
Destination search
    ->
Destination selected
    ->
Routing provider
    ->
Candidate routes
    ->
Safety analysis
    ->
Fastest / Balanced / Safety Priority
    ->
Route comparison
    ->
User selects route
    ->
Optional Safe Trip

---

## 2. Route Comparison

Each candidate route can display:

- ETA
- distance
- contextual safety indicators
- incident activity
- activity/isolation indicators
- emergency accessibility
- explanation of major contributing factors

Do not describe a route as guaranteed safe.

---

## 3. Safe Trip

Start Safe Trip
    ->
Capture selected route
    ->
Set expected arrival
    ->
Optional trusted-contact sharing
    ->
Start journey
    ->
Track location according to settings
    ->
Monitor route
    ->
Detect significant deviation
    ->
Ask user if they are okay
    ->
I'm Safe / Need Help
    ->
Continue or escalate
    ->
Trip completion

---

## 4. Route Deviation

Location update
    ->
Compare current position with planned route
    ->
Determine whether deviation is significant
    ->
If no:
        continue monitoring

If yes:
        ask user whether they are okay

Actions:

I'm Safe
    ->
Continue trip

Need Help
    ->
Offer assistance / emergency workflow

A deviation alone is not proof of an emergency.

---

## 5. Check-In

User starts journey
    ->
Expected arrival configured
    ->
Journey continues
    ->
Arrival confirmed

OR

Expected arrival passes
    ->
Prompt user
    ->
I'm Safe / Need Help

---

## 6. Trusted Contacts

Settings
    ->
Trusted Contacts
    ->
Add contact
    ->
Configure sharing preference
    ->
Save

Possible operations:

- create
- list
- update
- delete

---

## 7. SOS

Hold SOS
    ->
Confirm intentional activation
    ->
Create emergency event
    ->
Capture current location
    ->
Notify configured contacts
    ->
Show nearby emergency resources
    ->
Continue location sharing according to settings
    ->
Emergency remains ACTIVE
    ->
ACKNOWLEDGED
    ->
RESOLVED

---

## 8. Find Assistance

User requests help
    ->
Query nearby resources
    ->
Filter by availability where possible
    ->
Rank by distance and contextual indicators
    ->
Display options
    ->
Navigate to selected location

---

## 9. Community Report

User selects report
    ->
Select category
    ->
Add description
    ->
Capture location
    ->
Submit
    ->
Validate
    ->
Store report
    ->
Apply confidence
    ->
Safety engine can use report

---

## 10. AI Incident Classification

Free-text report
    ->
AI classification
    ->
Structured incident candidate
    ->
Validation
    ->
Persist
    ->
Safety engine

AI should not bypass validation.

---

## 11. Privacy

User
    ->
Privacy settings
    ->
Configure:

- live location sharing
- trusted contact sharing
- emergency sharing
- retention

Settings
    ->
Stored
    ->
Applied by services

---

## 12. Emergency State

ACTIVE
    |
    v
ACKNOWLEDGED
    |
    v
RESOLVED

Only authorized operations may transition emergency state.

---

## 13. Demo Flow

Recommended hackathon demonstration:

1. Open Nivara.
2. Allow/select current location.
3. Search destination.
4. Display candidate routes.
5. Compare Fastest, Balanced and Safety Priority.
6. Show contextual indicators.
7. Start Safe Trip.
8. Simulate route deviation.
9. Show check-in prompt.
10. Demonstrate trusted contacts.
11. Demonstrate SOS flow.
12. Show nearby assistance resources.
13. Submit a community report.
14. Show report reflected in safety intelligence.
EOF

echo "[5/8] Creating API documentation..."

cat > docs/api.md <<'EOF'
# Nivara API

Base path:

/api/v1

The exact request and response schemas must be maintained by the implementation team as the backend evolves.

---

## Health

GET /health

Purpose:

Verify that the backend is running.

---

## Routes

POST /routes

Purpose:

Calculate candidate routes between origin and destination.

Potential inputs:

- origin
- destination
- routing mode
- travel preferences

Potential output:

- candidate routes
- ETA
- distance
- geometry
- safety indicators

---

GET /routes/{route_id}

Purpose:

Retrieve a previously generated route.

---

## Safety

GET /safety/score

Purpose:

Retrieve contextual safety indicators for a location or route segment.

---

GET /safety/heatmap

Purpose:

Retrieve contextual safety data suitable for map visualization.

---

## Incidents

GET /incidents

Purpose:

Retrieve incidents near a location or within a spatial region.

---

POST /incidents/reports

Purpose:

Submit a community incident report.

---

GET /incidents/{incident_id}

Purpose:

Retrieve a specific incident.

---

## Trips

POST /trips

Purpose:

Create a Safe Trip.

---

GET /trips/{trip_id}

Purpose:

Retrieve trip state.

---

POST /trips/{trip_id}/start

Purpose:

Start monitoring a Safe Trip.

---

POST /trips/{trip_id}/check-in

Purpose:

Record a user check-in.

---

POST /trips/{trip_id}/complete

Purpose:

Complete a Safe Trip.

---

## Trusted Contacts

GET /trusted-contacts

Purpose:

List configured trusted contacts.

---

POST /trusted-contacts

Purpose:

Create a trusted contact.

---

PATCH /trusted-contacts/{contact_id}

Purpose:

Update a trusted contact.

---

DELETE /trusted-contacts/{contact_id}

Purpose:

Delete a trusted contact.

---

## Emergency

POST /emergency/sos

Purpose:

Create an emergency event.

---

GET /emergency/{event_id}

Purpose:

Retrieve emergency event state.

---

POST /emergency/{event_id}/acknowledge

Purpose:

Acknowledge an emergency event.

---

POST /emergency/{event_id}/resolve

Purpose:

Resolve an emergency event.

---

## Safe Places

GET /safe-places

Purpose:

Find nearby assistance resources.

Potential categories:

- hospital
- police station
- petrol pump
- hotel
- open business
- other assistance location

---

## Privacy

GET /privacy/settings

Purpose:

Retrieve current privacy configuration.

---

PATCH /privacy/settings

Purpose:

Update privacy configuration.

---

## API Rules

All endpoints should:

- validate input
- use appropriate HTTP status codes
- return structured errors
- avoid leaking sensitive information
- respect authorization
- respect privacy settings
EOF

echo "[6/8] Creating architectural decisions and task board..."

cat > docs/decisions.md <<'EOF'
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
EOF

cat > docs/tasks.md <<'EOF'
# Nivara Task Board

Status values:

- [ ] Not started
- [~] In progress
- [x] Completed
- [!] Blocked

---

# Foundation

- [ ] T001 Repository foundation
- [ ] T002 Frontend foundation
- [ ] T003 Backend foundation
- [ ] T004 Database foundation
- [ ] T005 Configuration/environment foundation
- [ ] T006 API foundation
- [ ] T007 Testing foundation

---

# Navigation

- [ ] T010 Map integration
- [ ] T011 Current location
- [ ] T012 Destination search
- [ ] T013 Routing integration
- [ ] T014 Route normalization
- [ ] T015 Safety scoring
- [ ] T016 Route comparison
- [ ] T017 Fastest mode
- [ ] T018 Balanced mode
- [ ] T019 Safety Priority mode
- [ ] T020 Safety heatmap

---

# Incidents

- [ ] T030 Incident model
- [ ] T031 Incident listing
- [ ] T032 Incident spatial queries
- [ ] T033 Community report creation
- [ ] T034 Community report validation
- [ ] T035 Confidence model
- [ ] T036 Incident filtering
- [ ] T037 Incident UI

---

# AI

- [ ] T040 AI incident classification
- [ ] T041 AI structured extraction
- [ ] T042 AI validation
- [ ] T043 AI failure handling

---

# Safe Trip

- [ ] T050 Safe Trip model
- [ ] T051 Safe Trip creation
- [ ] T052 Safe Trip start
- [ ] T053 Location tracking
- [ ] T054 Route deviation detection
- [ ] T055 Deviation UI
- [ ] T056 Check-in
- [ ] T057 Trip completion
- [ ] T058 Trip history

---

# Trusted Contacts

- [ ] T060 Trusted contact model
- [ ] T061 Create contact
- [ ] T062 List contacts
- [ ] T063 Update contact
- [ ] T064 Delete contact
- [ ] T065 Sharing preferences

---

# Emergency

- [ ] T070 Emergency model
- [ ] T071 SOS activation
- [ ] T072 Emergency state machine
- [ ] T073 Contact notification abstraction
- [ ] T074 Emergency resource discovery
- [ ] T075 Emergency UI
- [ ] T076 Emergency acknowledgement
- [ ] T077 Emergency resolution

---

# Safe Places

- [ ] T080 Nearby resource search
- [ ] T081 Resource filtering
- [ ] T082 Resource ranking
- [ ] T083 Navigation to resource

---

# Privacy

- [ ] T090 Privacy model
- [ ] T091 Location sharing controls
- [ ] T092 Trusted-contact sharing controls
- [ ] T093 Emergency sharing controls
- [ ] T094 Data retention policy
- [ ] T095 Sensitive logging review

---

# Integration

- [ ] T100 Navigation integration
- [ ] T101 Safety engine integration
- [ ] T102 Community reports integration
- [ ] T103 Safe Trip integration
- [ ] T104 Emergency integration
- [ ] T105 Privacy integration
- [ ] T106 Demo data
- [ ] T107 End-to-end testing
- [ ] T108 UI polish
- [ ] T109 Hackathon demo preparation

---

# Future

- [ ] T200 News ingestion
- [ ] T201 News extraction
- [ ] T202 News geocoding
- [ ] T203 News incident confidence
- [ ] T204 Advanced safety signals
EOF

cat > docs/transfer.md <<'EOF'
# Nivara Agent Transfer

## Current Status

Project context initialized.

Application implementation has not started.

---

## Last Completed Task

Repository context/bootstrap creation.

---

## Current Architecture

Frontend:

Next.js + TypeScript + Tailwind + shadcn/ui

Backend:

FastAPI + Python

Database:

PostgreSQL + PostGIS

Maps:

External provider

AI:

Incident classification and structured extraction

---

## Last Agent

Bootstrap agent.

---

## Files Created

- AGENTS.md
- docs/architecture.md
- docs/flow.md
- docs/api.md
- docs/decisions.md
- docs/tasks.md
- docs/transfer.md
- skills/security4her-backend/SKILL.md
- skills/security4her-frontend/SKILL.md
- skills/safety-engine/SKILL.md
- skills/agent-handoff/SKILL.md
- .gitignore

---

## Tests

No application tests exist yet.

Bootstrap script syntax should be verified with:

bash -n bootstrap-nivara.sh

---

## Known Issues

The application has not yet been implemented.

Frontend has not yet been initialized.

Backend has not yet been initialized.

Database has not yet been configured.

External integrations have not yet been configured.

---

## Next Task

T001 - Repository foundation.

The next agent should act as the founding principal engineer/architect and establish the minimal runnable frontend/backend/database foundation.

---

## Handoff Requirements

The next agent must:

1. Read AGENTS.md.
2. Inspect repository state.
3. Read relevant architecture documents.
4. Implement only the assigned foundation scope.
5. Run verification commands.
6. Update docs/tasks.md.
7. Update docs/transfer.md.
8. Review git diff.
9. Record the exact next task.
EOF

echo "[7/8] Creating agent skills..."

cat > skills/security4her-backend/SKILL.md <<'EOF'
---
name: security4her-backend
description: Build and maintain the Nivara FastAPI backend, services, repositories, APIs, validation, security, geospatial operations, and tests.
---

# Nivara Backend Skill

## Purpose

Use this skill when implementing or modifying the FastAPI backend.

---

## Architecture

Prefer:

API
 ->
Service
 ->
Repository
 ->
Database

---

## API Layer

Responsible for:

- HTTP routing
- request validation
- authentication
- authorization
- response serialization
- error mapping

Keep route handlers thin.

---

## Service Layer

Responsible for:

- business rules
- safety calculations
- trip state transitions
- emergency state transitions
- orchestration

---

## Repository Layer

Responsible for:

- database queries
- persistence
- PostGIS operations
- spatial filtering

---

## Rules

- Inspect before editing.
- Preserve existing interfaces.
- Use typed request/response models.
- Validate external input.
- Keep secrets out of source code.
- Treat location as sensitive.
- Avoid unnecessary logging of precise locations.
- Use appropriate HTTP status codes.
- Write meaningful tests.
- Keep business logic out of route handlers.
- Update docs/api.md when API contracts change.
- Update docs/tasks.md when tasks are completed.
- Update docs/transfer.md before handoff.

---

## Security

Never trust:

- client-provided authorization
- client-provided user IDs
- client-provided permissions
- unvalidated AI output

Authorization must be enforced server-side.

---

## Testing

Important backend tests include:

- service logic
- safety calculations
- state transitions
- API validation
- authorization
- repository behavior where practical
EOF

cat > skills/security4her-frontend/SKILL.md <<'EOF'
---
name: security4her-frontend
description: Build and maintain the Nivara Next.js frontend, navigation UX, map interfaces, safety indicators, Safe Trip, emergency flows, privacy controls, and responsive UI.
---

# Nivara Frontend Skill

## Stack

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

---

## Principles

Build a clear, fast and trustworthy safety interface.

Safety information should be understandable without being alarmist.

---

## Rules

- Inspect before editing.
- Reuse existing components.
- Keep components focused.
- Keep API access separated from presentation.
- Use TypeScript types for API data.
- Handle loading states.
- Handle error states.
- Handle empty states.
- Make important actions accessible.
- Avoid accidental SOS activation.
- Protect sensitive location information.
- Do not expose internal API secrets.
- Never present safety estimates as guarantees.
- Never label a location as objectively safe or dangerous.

---

## Navigation UI

Route options should make it easy to compare:

- travel time
- distance
- contextual safety indicators
- important contributing factors

Supported modes:

- Fastest
- Balanced
- Safety Priority

---

## Emergency UI

Emergency actions must be visually clear.

SOS should use an intentional activation mechanism.

Do not hide emergency actions behind confusing navigation.

---

## Testing

Test important user flows such as:

- destination search
- route selection
- Safe Trip
- deviation handling
- check-in
- SOS
- privacy controls
EOF

cat > skills/safety-engine/SKILL.md <<'EOF'
---
name: safety-engine
description: Implement Nivara contextual safety scoring, route comparison, incident weighting, geospatial signals, explainable safety indicators, and safety heatmaps.
---

# Nivara Safety Engine

## Purpose

Estimate contextual safety indicators for routes and locations.

The engine must never claim to predict whether harm will occur.

---

## Potential Signals

- incident density
- incident recency
- incident severity
- community report confidence
- time of day
- lighting indicators
- activity indicators
- open businesses
- emergency resources
- route isolation
- historical incident activity

---

## Routing Modes

### Fastest

Travel time has the strongest influence.

### Balanced

Travel time and contextual safety indicators are balanced.

### Safety Priority

Safety indicators receive substantially higher weight while preserving reasonable travel time.

---

## Design Principles

- Keep scoring configurable.
- Keep scoring explainable.
- Separate deterministic scoring from AI.
- Avoid unsupported probabilities.
- Do not use a single report as definitive truth.
- Account for incident recency.
- Account for confidence.
- Account for time context.
- Prefer normalized inputs.

---

## Example Concept

routeCost =
    timeWeight * normalizedTravelTime
    +
    safetyWeight * normalizedSafetyRisk
    +
    isolationWeight * normalizedIsolationRisk

The implementation may evolve.

Architectural changes must be documented.
EOF

cat > skills/agent-handoff/SKILL.md <<'EOF'
---
name: agent-handoff
description: Maintain Nivara multi-agent development state, task tracking, documentation, testing, git hygiene, and agent-to-agent handoff.
---

# Nivara Agent Handoff

## Purpose

Ensure that another agent can continue development without relying on chat history.

---

## Before Finishing

Run:

1. git status
2. git diff
3. relevant tests
4. relevant build/type checks

---

## Update

Update:

docs/tasks.md
docs/transfer.md

Also update:

docs/architecture.md
docs/api.md
docs/flow.md
docs/decisions.md

when relevant.

---

## Transfer Must Include

- current status
- last completed task
- files changed
- tests run
- verification commands
- known issues
- blockers
- next exact task

---

## Rules

- Do not claim tests passed unless actually run.
- Do not hide known failures.
- Do not overwrite another agent's work unnecessarily.
- Keep commits focused.
- Inspect git diff before handoff.
- Repository state is the source of truth.
EOF

echo "[8/8] Creating .gitignore and environment template..."

cat > .gitignore <<'EOF'
# Environment
.env
.env.*
!.env.example

# Node
node_modules/
.next/
dist/
out/
.turbo/

# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Testing
coverage/
htmlcov/
.coverage
.coverage.*

# IDE
.vscode/
.idea/

# Logs
*.log
logs/

# Databases
*.sqlite
*.sqlite3
*.db

# OS
.DS_Store
Thumbs.db

# Temporary
tmp/
temp/
EOF

cat > .env.example <<'EOF'
# Nivara environment configuration

# Backend
APP_ENV=development
APP_DEBUG=true

# Database
DATABASE_URL=postgresql+asyncpg://nivara:nivara@localhost:5432/nivara

# Map provider
MAP_API_KEY=

# AI provider
AI_API_KEY=

# Notifications
NOTIFICATION_PROVIDER=
NOTIFICATION_API_KEY=

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF

echo ""
echo "=========================================="
echo "       Nivara bootstrap complete!"
echo "=========================================="
echo ""
echo "Project root:"
echo "  ${PROJECT_ROOT}"
echo ""
echo "Created:"
echo "  AGENTS.md"
echo "  .gitignore"
echo "  .env.example"
echo "  docs/"
echo "  skills/"
echo "  frontend/"
echo "  backend/"
echo "  tests/"
echo "  scripts/"
echo ""
echo "Next verification:"
echo ""
echo "  bash -n bootstrap-nivara.sh"
echo "  tree -a"
echo ""
echo "Then initialize Git:"
echo ""
echo "  git init"
echo "  git add ."
echo '  git commit -m "chore: initialize Nivara project context"'
echo ""
echo "Next Codex task:"
echo "  T001 - Repository foundation"
echo ""
