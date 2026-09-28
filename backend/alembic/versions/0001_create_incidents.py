"""create incidents table

Revision ID: 0001_create_incidents
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision: str = "0001_create_incidents"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    incident_category = postgresql.ENUM(
        "harassment", "theft", "suspicious_activity", "poor_lighting", "unsafe_isolated_area", "other",
        name="incident_category", create_type=False,
    )
    incident_severity = postgresql.ENUM("low", "medium", "high", name="incident_severity", create_type=False)
    incident_source = postgresql.ENUM(
        "community_report", "official_report", "verified_partner", "imported_data", name="incident_source", create_type=False
    )
    confidence_level = postgresql.ENUM(
        "unverified", "corroborated", "higher_confidence", name="confidence_level", create_type=False
    )
    incident_status = postgresql.ENUM(
        "unverified", "corroborated", "validated", "rejected", name="incident_status", create_type=False
    )
    bind = op.get_bind()
    for enum in (incident_category, incident_severity, incident_source, confidence_level, incident_status):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("category", incident_category, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location", Geometry(geometry_type="POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("severity", incident_severity, nullable=False),
        sa.Column("source", incident_source, nullable=False),
        sa.Column("confidence_level", confidence_level, nullable=False),
        sa.Column("corroboration_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", incident_status, nullable=False),
        sa.Column("confidence_factors", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_incidents_latitude"),
        sa.CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_incidents_longitude"),
        sa.CheckConstraint("corroboration_count >= 0", name="ck_incidents_corroboration_count"),
    )
    for column in ("category", "occurred_at", "reported_at", "severity", "source", "confidence_level", "status"):
        op.create_index(f"ix_incidents_{column}", "incidents", [column])
    op.create_index("ix_incidents_location_gist", "incidents", ["location"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_index("ix_incidents_location_gist", table_name="incidents")
    for column in ("category", "occurred_at", "reported_at", "severity", "source", "confidence_level", "status"):
        op.drop_index(f"ix_incidents_{column}", table_name="incidents")
    op.drop_table("incidents")
    bind = op.get_bind()
    for name in ("incident_status", "confidence_level", "incident_source", "incident_severity", "incident_category"):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
