# Synthetic demo data

Nivara includes an explicit development seed for hackathon demonstrations.
It creates 36 deterministic incident records around an approximate demo
center near Priyadarshini College of Engineering, Nagpur. The repository does
not contain a verified campus coordinate; the center is only a compact map
visualization anchor and is not an exact location claim.

## Important disclaimer

Every record created by this seed is synthetic. It does not describe a real
incident, crime report, road, or area. It must not be presented as factual
real-world safety intelligence, and lower activity or empty cells must not be
interpreted as proof that an area is safe.

## Seed command

From the repository root:

```bash
cd backend
python scripts/seed_demo_data.py
```

The command uses the existing SQLAlchemy session and PostGIS point model. It
does not require OpenRouteService, AI, or any external provider. It fails
clearly if PostgreSQL/PostGIS is unavailable rather than reporting a false
success.

## Dataset shape

- 36 records in a compact approximately 1–3 km demonstration area.
- Existing categories include harassment, theft, suspicious activity, poor
  lighting, unsafe/isolated area, and other.
- Existing low, medium, and high severity values are represented.
- Existing unverified, corroborated, and higher-confidence levels are
  represented.
- Fixed past timestamps include relatively recent and older synthetic
  records; no timestamp is generated from the current clock.
- Dense, moderate, sparse, and intentionally empty spatial areas are created
  by the fixed coordinate offsets.

## Idempotency and reset behavior

Each record has a stable UUID derived from a fixed namespace and key. Running
the command again refreshes only those same demo IDs and never deletes or
modifies unrelated incident rows. There is no automatic reset or production
startup seeding.

The existing incident list and safety heatmap endpoints can be used after a
successful seed. Their existing contextual wording and safety disclaimer
remain authoritative; the seed does not change scoring or route comparison.
