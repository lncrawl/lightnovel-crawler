"""Merge VerifiedEmail to User

Revision ID: 0d1f6e13db1a
Revises: 4d43af0bd879
Create Date: 2026-03-08 19:20:00.947141
"""

from typing import Sequence, Union

import sqlmodel as sa
from alembic import op
from sqlmodel.sql.sqltypes import AutoString

# revision identifiers, used by Alembic.
revision: str = "0d1f6e13db1a"
down_revision: Union[str, Sequence[str], None] = "4d43af0bd879"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

try:
    dialect = op.get_context().dialect.name
except Exception:
    dialect = ""


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    conn = op.get_bind()
    value = 1 if dialect == "sqlite" else True
    conn.execute(sa.text(f"UPDATE users SET is_verified = {value} " "WHERE email IN (SELECT email FROM verifiedemail)"))

    op.drop_table("verifiedemail")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "verifiedemail",
        sa.Column("email", AutoString(), nullable=False),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("email", name=op.f("verifiedemail_pkey")),
    )

    conn = op.get_bind()
    value = 1 if dialect == "sqlite" else True
    conn.execute(
        sa.text(
            "INSERT INTO verifiedemail (email, created_at) "
            f"SELECT email, created_at FROM users WHERE is_verified = {value}"
        )
    )

    op.drop_column("users", "is_verified")
