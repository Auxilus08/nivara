"""create Safe Trip plans

Revision ID: 0002_create_safe_trips
Revises: 0001_create_incidents
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_create_safe_trips"
down_revision: Union[str, None] = "0001_create_incidents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safe_trips",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("selected_route_id", sa.String(length=255), nullable=False),
        sa.Column("origin_latitude", sa.Float(), nullable=False),
        sa.Column("origin_longitude", sa.Float(), nullable=False),
        sa.Column("destination_latitude", sa.Float(), nullable=False),
        sa.Column("destination_longitude", sa.Float(), nullable=False),
        sa.Column("route_distance_meters", sa.Float(), nullable=False),
        sa.Column("route_duration_seconds", sa.Integer(), nullable=False),
        sa.Column("route_geometry", postgresql.JSONB(), nullable=False),
        sa.Column("expected_arrival_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("origin_latitude >= -90 AND origin_latitude <= 90", name="ck_safe_trips_origin_latitude"),
        sa.CheckConstraint("origin_longitude >= -180 AND origin_longitude <= 180", name="ck_safe_trips_origin_longitude"),
        sa.CheckConstraint("destination_latitude >= -90 AND destination_latitude <= 90", name="ck_safe_trips_destination_latitude"),
        sa.CheckConstraint("destination_longitude >= -180 AND destination_longitude <= 180", name="ck_safe_trips_destination_longitude"),
        sa.CheckConstraint("route_distance_meters >= 0", name="ck_safe_trips_route_distance"),
        sa.CheckConstraint("route_duration_seconds >= 0", name="ck_safe_trips_route_duration"),
        sa.CheckConstraint("status = 'planned'", name="ck_safe_trips_status"),
    )
    op.create_index("ix_safe_trips_expected_arrival_at", "safe_trips", ["expected_arrival_at"])
    op.create_index("ix_safe_trips_status", "safe_trips", ["status"])


def downgrade() -> None:
    op.drop_index("ix_safe_trips_status", table_name="safe_trips")
    op.drop_index("ix_safe_trips_expected_arrival_at", table_name="safe_trips")
    op.drop_table("safe_trips")
