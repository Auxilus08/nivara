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
