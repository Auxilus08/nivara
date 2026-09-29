# Nivara API

Base path:

/api/v1

The exact request and response schemas must be maintained by the implementation team as the backend evolves.

---

## Health

GET /health

GET /api/v1/health

Purpose:

Verify that the backend is running.

The versioned endpoint is the preferred contract for clients. `/health` remains
available as a simple infrastructure probe.

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

Implemented contract: `POST /api/v1/routes`

Request body:

```json
{
  "origin": {"latitude": 12.9716, "longitude": 77.5946},
  "destination": {"latitude": 12.9352, "longitude": 77.6245},
  "mode": "fastest"
}
```

Supported modes are `fastest`, `balanced`, and `safety_priority`. The current
foundation validates the mode and coordinates and normalizes provider results
to Nivara-owned route objects containing route ID, origin, destination,
distance, duration, provider-neutral geometry, provider metadata, normalized
travel-time score, comparison cost, and optional `safety_assessment`.

The response also includes `selected_route_id` and a contextual
`comparison_explanation`. Candidates are compared using normalized travel time
and incident-derived safety assessments when every candidate has available
context. Missing safety context is reported explicitly and does not become a
zero-risk value.

If the configured provider is unsupported or its server-side API key is missing,
the endpoint returns `503` with a structured provider-neutral configuration
error. Rate limits return `429`; provider timeouts return `504`; provider HTTP
or response-shape errors return `502`. It never returns fabricated route data.

The current adapter uses openrouteservice's Directions GeoJSON endpoint:
`POST https://api.openrouteservice.org/v2/directions/driving-car/geojson`.
The server sends the API key in the `Authorization` header; it is never sent
from the frontend.

OpenRouteService alternative routes are requested with a bounded target count
of three. The provider may return fewer candidates depending on route length,
coverage, or provider constraints; the API never fabricates alternatives.

When incident context is available, route comparison uses the following
normalized objective:

`comparison_cost = time_weight * normalized_travel_score + safety_weight * risk_score`

where `normalized_travel_score = duration / maximum_candidate_duration * 100`.
Lower cost is the configured selection objective, not an objective safety
claim.

For `mode: "fastest"`, the configured objective is to prioritize shorter
travel time using weights of `time=0.90` and `safety=0.10`. Available
`safety_assessment` data remains visible in the response; FASTEST does not
discard contextual incident indicators. This is a user-selected travel-time
objective, not a guarantee that the route is objectively fastest or safest.

For `mode: "balanced"`, the configured objective uses `time=0.55` and
`safety=0.45`. It combines normalized travel time with the existing
SafetyEngine risk score, so neither a lower-risk candidate nor a faster
candidate automatically wins in every case. The mode balances available
travel-time and safety indicators; it does not identify a safe or objectively
best route.

For `mode: "safety_priority"`, the configured objective uses `time=0.25` and
`safety=0.75`. It places greater weight on available safety indicators than
travel time while still retaining a travel-time component. The result is a
lower-estimated-risk objective based on available incident data, not a safe,
dangerous, or guaranteed-protection route claim.

---

GET /routes/{route_id}

Purpose:

Retrieve a previously generated route.

---

## Geocoding

GET /geocoding/search

Implemented contract: `GET /api/v1/geocoding/search?q={query}`

Searches for a destination using the configured server-side geocoding
provider. `q` is required, must contain at least two non-whitespace characters,
and is limited to 200 characters. The backend returns at most five results.

Response:

```json
{
  "results": [
    {
      "suggestion_id": "provider-result-id",
      "label": "Example Place, Bengaluru",
      "coordinate": {"latitude": 12.9716, "longitude": 77.5946}
    }
  ],
  "count": 1
}
```

The frontend receives only Nivara-owned destination suggestions. Provider
credentials and raw provider payloads remain server-side. Empty searches return
`422`; no provider matches return `200` with an empty result list. Provider
configuration failures return `503`, rate limits return `429`, timeouts return
`504`, and provider HTTP or malformed-response failures return `502`.

The current concrete adapter uses the OpenRouteService/HeiGIT forward
geocoding endpoint `GET https://api.heigit.org/pelias/v1/search`, with the
existing server-side `ROUTING_API_KEY` sent in the `Authorization` header. It
passes only the normalized search text and a bounded result size to the
provider. This is separate from the existing directions base URL.

---

## Safety

## Safe Places

`GET /api/v1/safe-places/nearby?latitude={lat}&longitude={lon}&radius={metres}&category={category}`

Returns deterministically ranked, bounded synthetic demo assistance resources.
Supported categories are `hospital`, `police_station`, `petrol_pump`, `hotel`,
and `open_business`. Radius is greater than zero and at most 50,000 metres.
Results include distance and coordinates; no emergency phone numbers or safety
claims are returned. The response explicitly identifies the catalog as demo data.

## Privacy

`GET /api/v1/privacy/settings` and `PATCH /api/v1/privacy/settings`

The patch accepts `location_sharing_enabled`,
`trusted_contact_sharing_enabled`, and `emergency_sharing_enabled`. Defaults are
false. Because authentication/user storage is not implemented, these are
prototype-global in-process settings and are not user-isolated or durable.

## Emergency

`POST /api/v1/emergencies` creates an `active` emergency for an active Safe
Trip, captures the latest recorded trip location when available, and rejects a
second active/acknowledged emergency for the same trip with `409`.
`POST /api/v1/emergencies/{id}/acknowledge` and
`POST /api/v1/emergencies/{id}/resolve` implement the state machine
`active -> acknowledged -> resolved`, with direct `active -> resolved` also
allowed. Unknown IDs return `404`; invalid transitions return `409`.

The notification provider is deterministic mock-only and never sends SMS,
email, push, or emergency-service dispatch. Responses expose `notification_mode`
and `sharing_status`; when privacy sharing is disabled, the API reports
`sharing_disabled` and does not claim contact details were shared. Nearby
resource discovery is provided by `/api/v1/safe-places/nearby`; the existing
emergency resources endpoint remains limited to demo workflow placeholders.

GET /safety/score

Purpose:

Retrieve contextual safety indicators for a location or route segment.

---

GET /safety/heatmap

Purpose:

Retrieve bounded, aggregated incident-derived contextual indicators for a map
viewport.

Implemented contract: `GET /api/v1/safety/heatmap`. The request requires
`min_latitude`, `min_longitude`, `max_latitude`, and `max_longitude`. Each
latitude/longitude span must be between 0.02 and 2 degrees. Optional `rows`
and `columns` default to 8 and are bounded from 2 to 12.

The response contains only occupied coarse grid cells. Each cell includes its
center, the existing SafetyEngine `risk_score`, `risk_level`, incident count,
and assessment confidence. Empty cells are omitted; no incidents is not
treated as a low-risk assessment.

Example:

`GET /api/v1/safety/heatmap?min_latitude=12.90&min_longitude=77.55&max_latitude=12.95&max_longitude=77.60&rows=8&columns=8`

## Synthetic demo data

The development seed command creates explicitly marked synthetic incident
records for the Nivara hackathon demonstration around an approximate
Priyadarshini College of Engineering, Nagpur demo center. These records are
not factual reports or real-world safety intelligence. See `docs/demo-data.md`
for the seed command and idempotency behavior.

```json
{
  "bounds": {"min_latitude": 12.9, "min_longitude": 77.55, "max_latitude": 12.95, "max_longitude": 77.6},
  "rows": 8,
  "columns": 8,
  "points": [{
    "latitude": 12.928125,
    "longitude": 77.578125,
    "risk_score": 48,
    "risk_level": "moderate",
    "incident_count": 2,
    "confidence": "low"
  }],
  "incident_count": 2,
  "disclaimer": "This estimate is based on available incident data and is not a guarantee of safety."
}
```

Incidents are queried with a PostGIS bounding envelope and assigned
deterministically to coarse cells. Each occupied cell becomes an
`IncidentSignalContext` assessed by the canonical SafetyEngine; the heatmap
does not define a second scoring formula. Reporter identity, descriptions,
IDs, and internal moderation fields are not returned. Risk levels are
contextual indicators, not claims that a place is safe, unsafe, or dangerous.

---

## Incidents

GET /incidents

Purpose:

Retrieve incidents near a location or within a spatial region.

Implemented contract: `GET /api/v1/incidents`

Supported query parameters:

- `category`: `harassment`, `theft`, `suspicious_activity`, `poor_lighting`, `unsafe_isolated_area`, or `other`
- `severity`: `low`, `medium`, or `high`
- `status`: `unverified`, `corroborated`, `validated`, or `rejected`
- `confidence_level`: `unverified`, `corroborated`, or `higher_confidence`
- `occurred_from` and `occurred_to`: timezone-aware ISO timestamps
- `latitude`, `longitude`, and `radius_meters`: provide all three for a PostGIS radius query; radius is limited to 25–10,000 metres
- `limit`: 1–100, default 50

Responses contain public incident context only: location, category, description,
timestamps, severity, source, status, and explainable confidence details.
Reporter identity is not part of the incident response.

---

POST /incidents/reports

Purpose:

Submit a community incident report.

Implemented contract: `POST /api/v1/incidents/reports`

Request body:

```json
{
  "category": "harassment",
  "description": "A description with at least ten characters.",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "occurred_at": "2026-09-28T18:30:00Z",
  "severity": "medium"
}
```

`occurred_at` is optional and defaults to the server time. It must be
timezone-aware and not in the future. Community reports are initially marked
`unverified` with confidence factors explaining that they are single reports
not yet corroborated. The API returns `201 Created`.

---

GET /incidents/{incident_id}

Purpose:

Retrieve a specific incident.

Implemented contract: `GET /api/v1/incidents/{incident_id}`. Missing incidents
return `404`.

---

## Trips

### POST /trips

Purpose:

Create a Safe Trip.

Implemented contract: `POST /api/v1/trips`. The request captures the selected
route snapshot and a future, timezone-aware expected arrival time. The created
trip is persisted with `status: "planned"`. This endpoint does not start
monitoring or implement tracking, deviation detection, check-ins, completion,
history, contacts, notifications, or emergency workflows; those concerns use
separate lifecycle or feature endpoints. Route geometry endpoints must match
the submitted origin and destination.
Invalid or non-future arrival times return `422`.

---

GET /trips/{trip_id}

Purpose:

Retrieve trip state.

---

GET /trips/history

Purpose:

Review Safe Trip lifecycle history.

Implemented contract: `GET /api/v1/trips/history`. The response contains
newest-first lifecycle records with deterministic `created_at` and trip ID
ordering. Each item includes `id`, `status`, `created_at`, optional
`started_at`, optional `completed_at`, `expected_arrival_at`, `origin`, and
`destination`. It does not include route geometry, location updates,
check-ins, deviation assessments, or other internal fields. An empty history
returns `200` with `trips: []` and `count: 0`.

Authentication is not implemented in the current prototype, so this endpoint
returns all Safe Trip records accessible through the current backend session
model; it does not claim real user-specific isolation.

---

POST /trips/{trip_id}/start

Purpose:

Start monitoring a Safe Trip.

Implemented contract: `POST /api/v1/trips/{trip_id}/start`. The endpoint
accepts no client timestamp or tracking payload. A persisted `planned` trip
transitions to `active`; the server records `started_at` using a timezone-aware
UTC timestamp and returns the complete updated trip snapshot. Missing trips
return `404`. Starting an already active or otherwise non-planned trip returns
`409 Conflict`. The selected route snapshot and expected arrival are unchanged.

---

POST /trips/{trip_id}/check-ins

Purpose:

Record a user check-in.

Implemented contract: `POST /api/v1/trips/{trip_id}/check-ins`. The request
has no client-supplied timestamp. Only `active` trips accept a check-in;
planned and completed trips return `409`, and missing trips return `404`. The
server records an authoritative timezone-aware UTC `checked_in_at` timestamp
and returns only `id`, `trip_id`, and `checked_in_at`. Repeated explicit
check-ins create separate records. A check-in is a user action and is not a
safety or emergency determination.

---

POST /trips/{trip_id}/locations

Purpose:

Record one current location update for an active Safe Trip.

Implemented contract: `POST /api/v1/trips/{trip_id}/locations`.

Request:

```json
{
  "latitude": 12.968,
  "longitude": 77.598,
  "recorded_at": "2026-09-29T12:00:00Z"
}
```

Only `active` trips accept updates. Planned and completed trips return `409`;
missing trips return `404`; invalid coordinates or timezone-naive timestamps
return `422`. The response contains only the persisted update: its ID, trip ID,
coordinates, device `recorded_at`, and server-generated `received_at`. It does
not return location history or perform route-deviation or safety analysis.

---

POST /trips/{trip_id}/complete

Purpose:

Complete a Safe Trip.

Implemented contract: `POST /api/v1/trips/{trip_id}/complete`. Only an active
trip can be completed; planned and already completed trips return `409`, and a
missing trip returns `404`. The server changes the lifecycle from `active` to
`completed`, assigns a timezone-aware UTC `completed_at`, and returns the
updated Safe Trip representation. No client timestamp is accepted. Completion
is an explicit user action and does not verify arrival or claim that the user
is safe.

---

GET /trips/{trip_id}/deviation

Purpose:

Evaluate the latest recorded location of an active Safe Trip against its
stored planned route geometry.

Implemented contract: `GET /api/v1/trips/{trip_id}/deviation`.

The response contains the trip ID, whether the latest location is outside the
configured route corridor, distance from the planned route in metres, the
configured threshold, the location update used, evaluation time, and a
contextual explanation. The current implementation uses the latest recorded
location only; it does not persist deviation state or apply hysteresis.

Active trips with no recorded location return `409` because deviation status
is unavailable. Missing trips return `404`, and planned or completed trips
return `409`. Deviation is route-adherence information, not a safety score or
an emergency determination. The frontend presents this assessment and does
not calculate deviation independently.

---

## Trusted Contacts

GET /api/v1/trusted-contacts

Purpose:

List configured trusted contacts.

Implemented contract: `GET /api/v1/trusted-contacts`. Returns only active
contacts in deterministic newest-first order (`created_at DESC`, then ID
descending) and returns `200` with an empty collection when none exist. The
prototype returns at most 100 contacts; `count` is the number of returned
items. No pagination parameter is currently exposed.

---

POST /api/v1/trusted-contacts

Purpose:

Create a trusted contact.

Implemented contract: `POST /api/v1/trusted-contacts`. The request requires a
bounded non-empty name, `contact_method` of `email` or `phone`, and a
structurally valid contact value. It returns the created contact with `201`.
This endpoint stores contact data only; it does not send notifications.

---

PATCH /api/v1/trusted-contacts/{contact_id}

Purpose:

Partially update an active trusted contact.

The request may contain any non-empty subset of `name`, `contact_method`, and
`contact_value`. The resulting method/value combination is validated using the
same email and phone rules as creation. Empty patches, invalid combinations,
unknown contacts, and inactive contacts are rejected with `422` or `404` as
appropriate. The contact ID and `created_at` remain unchanged; `updated_at` is
updated by the service. Existing Safe Trip associations and sharing
preferences remain attached to the same contact ID.

---

GET /api/v1/trusted-contacts/{contact_id}

Purpose:

Retrieve one active trusted contact. Unknown or deactivated contacts return
`404`.

---

DELETE /api/v1/trusted-contacts/{contact_id}

Purpose:

Deactivate a trusted contact. The endpoint returns `204`; repeated deletion or
unknown contacts return `404`. Deactivated contacts are not returned by list or
get endpoints. DELETE is soft deactivation: the database row, preferences, and
historical Safe Trip associations remain intact.

The response includes only the contact management fields: ID, name, method,
value, active state, and timestamps. No provider identifiers, user foreign key,
Safe Trip data, or delivery behavior is exposed. Authentication is not yet
implemented, so prototype access is not user-isolated.

### Safe Trip trusted-contact selections

`POST /api/v1/trips/{trip_id}/trusted-contacts` associates an existing active
trusted contact with a planned or active Safe Trip. The request body is
`{"trusted_contact_id": "..."}` and the response includes the trip/contact
IDs, association timestamp, and the intentionally selected contact fields.
Unknown trips or contacts return `404`; inactive contacts cannot be selected;
completed trips and duplicate selections return `409`.

`GET /api/v1/trips/{trip_id}/trusted-contacts` returns the selected active
contacts for a trip and returns an empty collection when none are selected.

`DELETE /api/v1/trips/{trip_id}/trusted-contacts/{contact_id}` removes only the
association and returns `204`. It never deletes the Trusted Contact itself.
Completed trips cannot be modified. These endpoints persist only the
association and do not send notifications or expose location data. Authentication
is not implemented, so prototype user-level isolation cannot be enforced.

### Sharing preferences

`GET /api/v1/trusted-contacts/{contact_id}/sharing-preferences` returns the
contact's explicit future-sharing permissions. If no preference row exists for
an active contact, the service initializes a restrictive default with all
permissions false.

`PATCH /api/v1/trusted-contacts/{contact_id}/sharing-preferences` accepts a
non-empty partial object containing `allow_trip_status`, `allow_location`,
and/or `allow_emergency`. All values default to false and unknown or inactive
contacts return `404`; empty patches return `422`.

`allow_trip_status` controls whether future supported workflows may share Safe
Trip lifecycle updates; `allow_location` controls future location sharing;
and `allow_emergency` controls future emergency-related sharing. These flags
do not send notifications or transmit data today. Preference responses expose
the contact ID, three permission fields, and timestamps only.

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

## Frontend Map Visualization

The navigation page uses a client-only Leaflet map with OpenStreetMap-compatible
development tiles. It visualizes the normalized latitude/longitude route
geometry returned by `POST /api/v1/routes`, the selected destination, the
explicitly captured browser location, and the backend heatmap response when the
user requests contextual indicators.

The frontend does not call OpenRouteService, calculate routes or durations,
choose routes, or calculate safety values. `ROUTING_API_KEY` remains server-side;
no `NEXT_PUBLIC_*` routing or map credential is required. Route and heatmap
unavailability leaves the map usable without fabricating geometry or safety
values.

## API Rules

All endpoints should:

- validate input
- use appropriate HTTP status codes
- return structured errors
- avoid leaking sensitive information
- respect authorization
- respect privacy settings

## Emergency workflow

`POST /api/v1/emergencies` creates an explicit emergency record. A trip-linked
SOS requires an active Safe Trip, rejects duplicate active/acknowledged
emergencies with `409`, and captures the latest stored trip location when one
exists. `trip_id` is optional for a standalone demo SOS.

`POST /api/v1/emergencies/{id}/acknowledge` permits `active -> acknowledged`.
`POST /api/v1/emergencies/{id}/resolve` permits `active -> resolved` and
`acknowledged -> resolved`. Invalid transitions return `409`; unknown records
return `404`. Lifecycle timestamps are server-generated and timezone-aware.

`GET /api/v1/emergencies/resources` returns deterministic demo placeholders.
No real emergency number, dispatch integration, SMS/email delivery, or
guaranteed response is provided. Emergency responses identify the notification
mode as `mock_demo_only`; the mock provider records a minimal action without
contacting trusted contacts.
