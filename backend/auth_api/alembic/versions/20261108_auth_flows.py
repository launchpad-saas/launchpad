"""add refresh families, action tokens and login throttling

Revision ID: 20261108_auth_flows
Revises: e0ec1352c70a
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20261108_auth_flows"
down_revision: Union[str, None] = "e0ec1352c70a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "tenant_id", existing_type=sa.UUID(), nullable=True)
    op.create_index(
        "uq_users_tenant_email_ci",
        "users",
        ["tenant_id", sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NOT NULL"),
    )
    op.create_index(
        "uq_users_platform_email_ci",
        "users",
        [sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL"),
    )

    op.add_column("sessions", sa.Column("family_id", sa.UUID(), nullable=True))
    op.execute("UPDATE sessions SET family_id = id WHERE family_id IS NULL")
    op.alter_column("sessions", "family_id", existing_type=sa.UUID(), nullable=False)
    op.add_column("sessions", sa.Column("replaced_by_session_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_sessions_replaced_by_session_id_sessions",
        "sessions",
        "sessions",
        ["replaced_by_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_sessions_family_id", "sessions", ["family_id"], unique=False)

    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "purpose IN ('email_verification', 'password_reset')",
            name="ck_auth_tokens_purpose",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"], unique=False)
    op.create_index(
        "ix_auth_tokens_user_purpose",
        "auth_tokens",
        ["user_id", "purpose"],
        unique=False,
    )

    op.create_table(
        "login_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_login_attempts_email_time",
        "login_attempts",
        ["email", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_login_attempts_ip_time",
        "login_attempts",
        ["ip_address", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_login_attempts_ip_time", table_name="login_attempts")
    op.drop_index("ix_login_attempts_email_time", table_name="login_attempts")
    op.drop_table("login_attempts")

    op.drop_index("ix_auth_tokens_user_purpose", table_name="auth_tokens")
    op.drop_index("ix_auth_tokens_user_id", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    op.drop_index("uq_users_platform_email_ci", table_name="users")
    op.drop_index("uq_users_tenant_email_ci", table_name="users")

    op.drop_index("ix_sessions_family_id", table_name="sessions")
    op.drop_constraint(
        "fk_sessions_replaced_by_session_id_sessions",
        "sessions",
        type_="foreignkey",
    )
    op.drop_column("sessions", "replaced_by_session_id")
    op.drop_column("sessions", "family_id")
    op.alter_column("users", "tenant_id", existing_type=sa.UUID(), nullable=False)
