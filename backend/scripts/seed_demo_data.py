"""Idempotently seed synthetic incident data for the Nivara hackathon demo.

This module intentionally does not run during application startup.  Every
record is synthetic and carries the stable ``[DEMO]`` marker in its
description; the data must never be interpreted as a factual incident report.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence
from uuid import UUID, uuid5

from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Allow the documented direct-script command when run from the backend
# directory, while keeping normal package imports unchanged.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionFactory
from app.models.incident import (
    ConfidenceLevel,
    Incident,
    IncidentCategory,
    IncidentSeverity,
    IncidentSource,
    IncidentStatus,
)


DEMO_DESCRIPTION_PREFIX = "[DEMO] Synthetic incident for Nivara hackathon demonstration."
DEMO_NAMESPACE = UUID("5a9d47c3-4ef7-4f7c-84d2-4b5f3e9d5a11")

# No verified coordinate for Priyadarshini College of Engineering is stored in
# this repository.  This is an approximate, compact demo center only, not a
# claim about the exact campus location.
DEMO_CENTER_LATITUDE = 21.1800
DEMO_CENTER_LONGITUDE = 79.0600
DEMO_REFERENCE_AT = datetime(2026, 9, 1, 12, tzinfo=timezone.utc)


@dataclass(frozen=True)
class DemoIncidentSpec:
    key: str
    latitude_offset: float
    longitude_offset: float
    category: IncidentCategory
    severity: IncidentSeverity
    confidence_level: ConfidenceLevel
    status: IncidentStatus
    occurred_at: datetime


def _spec(
    key: str,
    latitude_offset: float,
    longitude_offset: float,
    category: IncidentCategory,
    severity: IncidentSeverity,
    confidence_level: ConfidenceLevel,
    status: IncidentStatus,
    occurred_at: datetime,
) -> DemoIncidentSpec:
    return DemoIncidentSpec(
        key=key,
        latitude_offset=latitude_offset,
        longitude_offset=longitude_offset,
        category=category,
        severity=severity,
        confidence_level=confidence_level,
        status=status,
        occurred_at=occurred_at,
    )


def demo_incident_specs() -> tuple[DemoIncidentSpec, ...]:
    """Return the fixed spatial, temporal, and signal distribution."""

    recent = DEMO_REFERENCE_AT
    recent_older = DEMO_REFERENCE_AT - timedelta(days=7)
    older = DEMO_REFERENCE_AT - timedelta(days=78)
    return (
        # Cluster A: dense demonstration cluster near the approximate center.
        _spec("cluster-a-01", 0.0010, 0.0005, IncidentCategory.HARASSMENT, IncidentSeverity.HIGH, ConfidenceLevel.HIGHER_CONFIDENCE, IncidentStatus.VALIDATED, recent),
        _spec("cluster-a-02", 0.0015, -0.0010, IncidentCategory.THEFT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent),
        _spec("cluster-a-03", -0.0010, 0.0015, IncidentCategory.SUSPICIOUS_ACTIVITY, IncidentSeverity.MEDIUM, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, recent_older),
        _spec("cluster-a-04", -0.0020, -0.0015, IncidentCategory.POOR_LIGHTING, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-a-05", 0.0025, 0.0020, IncidentCategory.UNSAFE_ISOLATED_AREA, IncidentSeverity.HIGH, ConfidenceLevel.HIGHER_CONFIDENCE, IncidentStatus.VALIDATED, recent),
        _spec("cluster-a-06", 0.0030, -0.0025, IncidentCategory.OTHER, IncidentSeverity.LOW, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, older),
        _spec("cluster-a-07", -0.0035, 0.0030, IncidentCategory.HARASSMENT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
        _spec("cluster-a-08", 0.0040, 0.0000, IncidentCategory.THEFT, IncidentSeverity.HIGH, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-a-09", -0.0045, -0.0035, IncidentCategory.SUSPICIOUS_ACTIVITY, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-a-10", 0.0050, 0.0040, IncidentCategory.POOR_LIGHTING, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
        _spec("cluster-a-11", -0.0055, 0.0010, IncidentCategory.UNSAFE_ISOLATED_AREA, IncidentSeverity.HIGH, ConfidenceLevel.HIGHER_CONFIDENCE, IncidentStatus.VALIDATED, recent),
        _spec("cluster-a-12", 0.0060, -0.0045, IncidentCategory.OTHER, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        # Cluster B: moderate activity to create a distinct heatmap pattern.
        _spec("cluster-b-01", -0.0080, -0.0060, IncidentCategory.THEFT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
        _spec("cluster-b-02", -0.0090, -0.0075, IncidentCategory.HARASSMENT, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-b-03", -0.0100, -0.0050, IncidentCategory.POOR_LIGHTING, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent),
        _spec("cluster-b-04", -0.0110, -0.0085, IncidentCategory.SUSPICIOUS_ACTIVITY, IncidentSeverity.HIGH, ConfidenceLevel.HIGHER_CONFIDENCE, IncidentStatus.VALIDATED, recent),
        _spec("cluster-b-05", -0.0120, -0.0065, IncidentCategory.UNSAFE_ISOLATED_AREA, IncidentSeverity.MEDIUM, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-b-06", -0.0130, -0.0095, IncidentCategory.OTHER, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-b-07", -0.0140, -0.0040, IncidentCategory.THEFT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
        _spec("cluster-b-08", -0.0150, -0.0070, IncidentCategory.HARASSMENT, IncidentSeverity.HIGH, ConfidenceLevel.HIGHER_CONFIDENCE, IncidentStatus.VALIDATED, recent),
        # Cluster C: sparse activity, with intentionally empty space between clusters.
        _spec("cluster-c-01", 0.0100, 0.0120, IncidentCategory.POOR_LIGHTING, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-c-02", 0.0115, 0.0135, IncidentCategory.SUSPICIOUS_ACTIVITY, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
        _spec("cluster-c-03", 0.0130, 0.0110, IncidentCategory.OTHER, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("cluster-c-04", 0.0145, 0.0145, IncidentCategory.THEFT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, older),
        _spec("cluster-c-05", 0.0160, 0.0125, IncidentCategory.HARASSMENT, IncidentSeverity.HIGH, ConfidenceLevel.HIGHER_CONFIDENCE, IncidentStatus.VALIDATED, recent),
        _spec("cluster-c-06", 0.0170, 0.0155, IncidentCategory.UNSAFE_ISOLATED_AREA, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        # Sparse perimeter points help demonstrate that the dataset is not a uniform blob.
        _spec("sparse-01", -0.0170, 0.0140, IncidentCategory.POOR_LIGHTING, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("sparse-02", 0.0180, -0.0140, IncidentCategory.THEFT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
        _spec("sparse-03", -0.0180, -0.0150, IncidentCategory.SUSPICIOUS_ACTIVITY, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("sparse-04", 0.0200, 0.0000, IncidentCategory.OTHER, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("sparse-05", -0.0200, 0.0020, IncidentCategory.HARASSMENT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
        _spec("sparse-06", 0.0020, -0.0200, IncidentCategory.UNSAFE_ISOLATED_AREA, IncidentSeverity.HIGH, ConfidenceLevel.HIGHER_CONFIDENCE, IncidentStatus.VALIDATED, recent),
        _spec("sparse-07", -0.0030, 0.0200, IncidentCategory.POOR_LIGHTING, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("sparse-08", 0.0200, 0.0200, IncidentCategory.THEFT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, older),
        _spec("sparse-09", -0.0200, -0.0200, IncidentCategory.SUSPICIOUS_ACTIVITY, IncidentSeverity.LOW, ConfidenceLevel.UNVERIFIED, IncidentStatus.UNVERIFIED, older),
        _spec("sparse-10", 0.0080, -0.0180, IncidentCategory.HARASSMENT, IncidentSeverity.MEDIUM, ConfidenceLevel.CORROBORATED, IncidentStatus.CORROBORATED, recent_older),
    )


def demo_incident_id(spec: DemoIncidentSpec) -> UUID:
    return uuid5(DEMO_NAMESPACE, spec.key)


def build_demo_incidents() -> list[Incident]:
    """Build the complete deterministic set without touching a database."""

    incidents: list[Incident] = []
    for spec in demo_incident_specs():
        latitude = DEMO_CENTER_LATITUDE + spec.latitude_offset
        longitude = DEMO_CENTER_LONGITUDE + spec.longitude_offset
        description = f"{DEMO_DESCRIPTION_PREFIX} Example {spec.category.value} indicator in a demo cluster; not a factual report."
        incidents.append(
            Incident(
                id=demo_incident_id(spec),
                category=spec.category,
                description=description,
                latitude=latitude,
                longitude=longitude,
                location=WKTElement(f"POINT({longitude} {latitude})", srid=4326),
                occurred_at=spec.occurred_at,
                reported_at=spec.occurred_at,
                severity=spec.severity,
                source=IncidentSource.IMPORTED_DATA,
                confidence_level=spec.confidence_level,
                corroboration_count=2 if spec.confidence_level == ConfidenceLevel.CORROBORATED else 0,
                status=spec.status,
                confidence_factors=["fixed synthetic demo dataset", f"configured level: {spec.confidence_level.value}"],
                created_at=spec.occurred_at,
                updated_at=spec.occurred_at,
            )
        )
    return incidents


def merge_demo_incidents(existing: Sequence[Incident]) -> list[Incident]:
    """Return an idempotent merge that preserves non-demo records."""

    merged = list(existing)
    by_id = {incident.id: incident for incident in merged}
    for desired in build_demo_incidents():
        current = by_id.get(desired.id)
        if current is None:
            merged.append(desired)
            continue
        for field in (
            "category", "description", "latitude", "longitude", "location", "occurred_at",
            "reported_at", "severity", "source", "confidence_level", "corroboration_count",
            "status", "confidence_factors", "created_at", "updated_at",
        ):
            setattr(current, field, getattr(desired, field))
    return merged


async def seed_demo_data(session: AsyncSession) -> int:
    """Upsert only this seed's stable IDs and return the dataset size."""

    desired = build_demo_incidents()
    result = await session.execute(select(Incident).where(Incident.id.in_([item.id for item in desired])))
    existing = {incident.id: incident for incident in result.scalars().all()}
    for item in desired:
        current = existing.get(item.id)
        if current is None:
            session.add(item)
        else:
            for field in (
                "category", "description", "latitude", "longitude", "location", "occurred_at",
                "reported_at", "severity", "source", "confidence_level", "corroboration_count",
                "status", "confidence_factors", "created_at", "updated_at",
            ):
                setattr(current, field, getattr(item, field))
    await session.commit()
    return len(desired)


async def _run() -> None:
    async with SessionFactory() as session:
        count = await seed_demo_data(session)
    print(f"Seeded {count} deterministic synthetic incidents (demo data only).")


def main() -> None:
    try:
        asyncio.run(_run())
    except Exception as exc:
        raise SystemExit(
            f"Demo seed failed: {exc}. Verify that PostgreSQL/PostGIS is running and the migration chain is current."
        ) from exc


if __name__ == "__main__":
    main()
