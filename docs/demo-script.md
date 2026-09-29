# Nivara hackathon demo script

This is a 3–5 minute demonstration of the working local product. Nivara uses
contextual indicators and synthetic demo incident data; it does not guarantee
personal safety.

## Start the application

The backend reads `.env` from its working directory. The startup command below
optionally sources the repository-root `.env` before launching the backend. Use
two terminals from the repository root:

Terminal 1:

```bash
cd backend
python -m pip install -e '.[test]'
if [ -f ../.env ]; then set -a; . ../.env; set +a; fi
alembic upgrade head
uvicorn app.main:app --reload
```

Terminal 2:

```bash
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000`. The backend API is expected at the configured
`NEXT_PUBLIC_API_URL` (the checked-in environment uses
`http://localhost:8000/api/v1`). If PostgreSQL/PostGIS or OpenRouteService is
not available, the UI shows an explicit unavailable/configuration error; it
does not fabricate route success.

If the database is available and migrations are current, seed the synthetic
incident dataset once:

```bash
cd backend
python scripts/seed_demo_data.py
```

The seed is idempotent and only updates its stable synthetic IDs. Never present
these incidents as factual reports.

## 1. Problem and concept

“Standard navigation optimizes time and distance. Nivara adds a contextual
safety-intelligence layer so people can compare travel efficiency with available
incident indicators, then protect the selected journey.”

## 2. Destination and route comparison

1. Click **Use current location** and allow browser location, or show the
   permission/unavailable error honestly if permission is denied.
2. Search for a destination and select a result.
3. Request a route.
4. Switch between **Fastest**, **Balanced**, and **Safety priority**. Explain
   that the modes change deterministic time/safety weighting; none means “safe”
   and Safety priority is not simply “the longest route.”

## 3. Safety context

1. Click **Show contextual indicators**.
2. Point out the **DEMO DATA** label, heatmap, contextual risk levels, incident
   counts, and confidence/disclaimer.
3. In the incident panel, submit a short demo community report. Explain that a
   new report starts unverified and the route/safety context is refreshed only
   when a route is already available.

## 4. Safe Trip and protection flow

1. Create a Safe Trip from the selected route and start it.
2. Record current location, refresh route status, and show the route-adherence
   or deviation result.
3. Check in.
4. Load Trusted Contacts and select a contact for the trip if one exists.
5. Load Privacy controls and show that sharing controls are disabled by default.
6. Trigger **SOS**, confirm the explicit demo action, and show the `ACTIVE`
   emergency state, location availability, and mock notification status.
7. Acknowledge, then resolve the emergency. Explain that no authority or real
   contact was notified.

## Jury questions

**Why not standard navigation?** Standard navigation primarily optimizes route
efficiency. Nivara compares that with contextual incident indicators and
journey-protection workflows.

**How is safety calculated?** The Safety Engine deterministically combines
incident density, recency, severity, confidence, and category activity into an
explainable contextual estimate. It is not a validated probability.

**How do route modes differ?** Fastest uses time/safety weights 0.90/0.10,
Balanced uses 0.55/0.45, and Safety Priority uses 0.25/0.75.

**How does Nivara avoid excessive detours?** Safety Priority retains a travel
time component and optimizes a multi-objective comparison rather than selecting
the longest route.

**What happens if safety data is unavailable?** The API says the indicators are
unavailable and the frontend shows that state; missing data is not treated as
zero risk.

**Is the incident data real?** No. The seeded hackathon dataset is explicitly
synthetic. Community reports are user-submitted and initially unverified.

**Does Nivara guarantee safety?** No. All results are contextual estimates and
not guarantees that an area or route is safe or dangerous.

**Does SOS send a real message?** No. The current provider is deterministic
mock-only and performs no SMS, email, push, or emergency-service dispatch.

**What happens if location permission is denied?** Nivara shows an error and
does not invent coordinates. Location-dependent actions remain unavailable until
the user supplies location through the supported flow.

**What data is stored?** The current backend can store incidents, Safe Trip
lifecycle/location/check-in records, trusted contacts, sharing preferences, and
emergency lifecycle records. Authentication, per-user ownership, automatic
retention, and deletion workflows are not implemented.

**What part is AI?** AI incident classification is planned but not implemented
in this MVP. Current scoring, routing comparison, validation, and state changes
are deterministic code.

## Known limitations

- Live PostgreSQL/PostGIS and OpenRouteService availability depend on the local
  environment and credentials.
- The prototype privacy settings are global in-process settings, not
  user-isolated settings.
- Safe Places and emergency resources are synthetic demo resources.
- No real notification or emergency dispatch integration exists.
