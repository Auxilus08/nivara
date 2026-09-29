"""create trusted contact sharing preferences

Revision ID: 0009_create_trusted_contact_sharing_preferences
Revises: 0008_create_safe_trip_trusted_contacts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009_create_trusted_contact_sharing_preferences"
down_revision: Union[str, None] = "0008_create_safe_trip_trusted_contacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trusted_contact_sharing_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trusted_contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allow_trip_status", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_location", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("allow_emergency", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["trusted_contact_id"],
            ["trusted_contacts.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("trusted_contact_id", name="uq_trusted_contact_sharing_preferences_contact"),
    )


def downgrade() -> None:
    op.drop_table("trusted_contact_sharing_preferences")
