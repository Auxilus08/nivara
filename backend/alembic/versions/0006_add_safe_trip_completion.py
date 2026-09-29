"""add Safe Trip completion timestamp

Revision ID: 0006_add_safe_trip_completion
Revises: 0005_create_safe_trip_check_ins
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_add_safe_trip_completion"
down_revision: Union[str, None] = "0005_create_safe_trip_check_ins"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("safe_trips", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("safe_trips", "completed_at")
