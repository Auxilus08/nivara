"""create emergency workflow records

Revision ID: 0010_create_emergencies
Revises: 0009_create_trusted_contact_sharing_preferences
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010_create_emergencies"
down_revision: Union[str, None] = "0009_create_trusted_contact_sharing_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "emergencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("emergency_type", sa.String(length=64), nullable=False, server_default="sos"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["trip_id"], ["safe_trips.id"], ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('active', 'acknowledged', 'resolved')", name="ck_emergencies_status"),
        sa.CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_emergencies_latitude"),
        sa.CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_emergencies_longitude"),
    )
    op.create_index("ix_emergencies_trip_id", "emergencies", ["trip_id"])
    op.create_index("ix_emergencies_status", "emergencies", ["status"])


def downgrade() -> None:
    op.drop_index("ix_emergencies_status", table_name="emergencies")
    op.drop_index("ix_emergencies_trip_id", table_name="emergencies")
    op.drop_table("emergencies")
