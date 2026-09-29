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
history, contacts, notifications, or emergency workflows; those remain later
tasks. Route geometry endpoints must match the submitted origin and destination.
Invalid or non-future arrival times return `422`.

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
