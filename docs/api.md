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
