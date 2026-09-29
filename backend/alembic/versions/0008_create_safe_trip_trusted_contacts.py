"""create Safe Trip trusted-contact associations

Revision ID: 0008_create_safe_trip_trusted_contacts
Revises: 0007_create_trusted_contacts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008_create_safe_trip_trusted_contacts"
down_revision: Union[str, None] = "0007_create_trusted_contacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "safe_trip_trusted_contacts",
        sa.Column("safe_trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trusted_contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["safe_trip_id"], ["safe_trips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trusted_contact_id"], ["trusted_contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "safe_trip_id",
            "trusted_contact_id",
            name="pk_safe_trip_trusted_contacts",
        ),
    )
    op.create_index(
        "ix_safe_trip_trusted_contacts_trusted_contact_id",
        "safe_trip_trusted_contacts",
        ["trusted_contact_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_safe_trip_trusted_contacts_trusted_contact_id",
        table_name="safe_trip_trusted_contacts",
    )
    op.drop_table("safe_trip_trusted_contacts")
