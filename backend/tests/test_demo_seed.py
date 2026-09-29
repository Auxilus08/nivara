from datetime import datetime, timezone

from app.models.incident import ConfidenceLevel, Incident, IncidentCategory, IncidentSeverity
from uuid import UUID
from scripts.seed_demo_data import (
    DEMO_CENTER_LATITUDE,
    DEMO_CENTER_LONGITUDE,
    DEMO_DESCRIPTION_PREFIX,
    build_demo_incidents,
    merge_demo_incidents,
)


def test_demo_dataset_is_deterministic_and_bounded():
    first = build_demo_incidents()
    second = build_demo_incidents()

    assert len(first) == 36
    assert [item.id for item in first] == [item.id for item in second]
    assert [(item.latitude, item.longitude, item.occurred_at) for item in first] == [
        (item.latitude, item.longitude, item.occurred_at) for item in second
    ]
    assert max(abs(item.latitude - DEMO_CENTER_LATITUDE) for item in first) <= 0.020
    assert max(abs(item.longitude - DEMO_CENTER_LONGITUDE) for item in first) <= 0.020


def test_demo_dataset_exercises_existing_incident_dimensions():
    incidents = build_demo_incidents()

    assert len({item.category for item in incidents}) >= 5
    assert {item.severity for item in incidents} == set(IncidentSeverity)
    assert {item.confidence_level for item in incidents} == set(ConfidenceLevel)
    assert all(item.description.startswith(DEMO_DESCRIPTION_PREFIX) for item in incidents)
    assert all(item.occurred_at <= datetime.now(timezone.utc) for item in incidents)
    assert len({item.latitude for item in incidents}) > 10


def test_demo_merge_is_idempotent_and_preserves_non_demo_records():
    template = build_demo_incidents()[0]
    non_demo = Incident(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        category=template.category,
        description="A non-demo record with a stable ID.",
        latitude=template.latitude,
        longitude=template.longitude,
        location=None,
        occurred_at=template.occurred_at,
        reported_at=template.reported_at,
        severity=template.severity,
        source=template.source,
        confidence_level=template.confidence_level,
        corroboration_count=0,
        status=template.status,
        confidence_factors=[],
        created_at=template.created_at,
        updated_at=template.updated_at,
    )
    # The merge key is deterministic, so an existing record at a seed ID is
    # treated as the seed's own record and refreshed. A distinct non-demo ID
    # must remain untouched.
    merged_once = merge_demo_incidents([non_demo])
    merged_twice = merge_demo_incidents(merged_once)

    assert len(merged_once) == 37
    assert len(merged_twice) == 37
    assert sum(item.description == non_demo.description for item in merged_twice) == 1
    assert len({item.id for item in merged_twice}) == 37
