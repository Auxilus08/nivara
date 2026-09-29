"""add Safe Trip active lifecycle fields

Revision ID: 0003_add_safe_trip_start
Revises: 0002_create_safe_trips
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_safe_trip_start"
down_revision: Union[str, None] = "0002_create_safe_trips"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("safe_trips", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_constraint("ck_safe_trips_status", "safe_trips", type_="check")
    op.create_check_constraint(
        "ck_safe_trips_status",
        "safe_trips",
        "status IN ('planned', 'active', 'completed')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_safe_trips_status", "safe_trips", type_="check")
    op.create_check_constraint("ck_safe_trips_status", "safe_trips", "status = 'planned'")
    op.drop_column("safe_trips", "started_at")
