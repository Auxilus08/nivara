"""create Safe Trip check-ins

Revision ID: 0005_create_safe_trip_check_ins
Revises: 0004_create_safe_trip_locations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_create_safe_trip_check_ins"
down_revision: Union[str, None] = "0004_create_safe_trip_locations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safe_trip_check_ins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "checked_in_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["trip_id"], ["safe_trips.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_safe_trip_check_ins_trip_id", "safe_trip_check_ins", ["trip_id"])
    op.create_index("ix_safe_trip_check_ins_checked_in_at", "safe_trip_check_ins", ["checked_in_at"])


def downgrade() -> None:
    op.drop_index("ix_safe_trip_check_ins_checked_in_at", table_name="safe_trip_check_ins")
    op.drop_index("ix_safe_trip_check_ins_trip_id", table_name="safe_trip_check_ins")
    op.drop_table("safe_trip_check_ins")
