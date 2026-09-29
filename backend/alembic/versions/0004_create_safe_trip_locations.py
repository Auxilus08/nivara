"""create Safe Trip location updates

Revision ID: 0004_create_safe_trip_locations
Revises: 0003_add_safe_trip_start
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0004_create_safe_trip_locations"
down_revision: Union[str, None] = "0003_add_safe_trip_start"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safe_trip_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "location",
            Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_safe_trip_locations_latitude"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_safe_trip_locations_longitude"),
        sa.ForeignKeyConstraint(["trip_id"], ["safe_trips.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_safe_trip_locations_trip_id", "safe_trip_locations", ["trip_id"])
    op.create_index("ix_safe_trip_locations_recorded_at", "safe_trip_locations", ["recorded_at"])
    op.create_index(
        "ix_safe_trip_locations_location_gist",
        "safe_trip_locations",
        ["location"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("ix_safe_trip_locations_location_gist", table_name="safe_trip_locations")
    op.drop_index("ix_safe_trip_locations_recorded_at", table_name="safe_trip_locations")
    op.drop_index("ix_safe_trip_locations_trip_id", table_name="safe_trip_locations")
    op.drop_table("safe_trip_locations")
