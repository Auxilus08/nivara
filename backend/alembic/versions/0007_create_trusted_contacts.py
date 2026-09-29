"""create trusted contacts

Revision ID: 0007_create_trusted_contacts
Revises: 0006_add_safe_trip_completion
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007_create_trusted_contacts"
down_revision: Union[str, None] = "0006_add_safe_trip_completion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trusted_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("contact_method", sa.String(length=16), nullable=False),
        sa.Column("contact_value", sa.String(length=320), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("contact_method IN ('phone', 'email')", name="ck_trusted_contacts_method"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_trusted_contacts_name"),
        sa.CheckConstraint("length(trim(contact_value)) > 0", name="ck_trusted_contacts_value"),
    )
    op.create_index("ix_trusted_contacts_is_active", "trusted_contacts", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_trusted_contacts_is_active", table_name="trusted_contacts")
    op.drop_table("trusted_contacts")
