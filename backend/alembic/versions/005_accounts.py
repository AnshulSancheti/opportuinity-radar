"""Accounts, revocable sessions, and authentication throttling.

Legacy anonymous actions remain unclaimed and are never exposed to accounts.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("accounts", sa.Column("id", UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(254), nullable=False, unique=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("password_hash", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("account_sessions", sa.Column("token_hash", sa.String(64), primary_key=True), sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_account_sessions_user_id", "account_sessions", ["user_id"])
    op.create_table("auth_attempts", sa.Column("id", sa.BigInteger(), primary_key=True), sa.Column("key", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_auth_attempts_key", "auth_attempts", ["key"])
    op.create_index("ix_auth_attempts_created_at", "auth_attempts", ["created_at"])
    op.create_index("ix_user_actions_owner", "user_actions", ["user_id"])


def downgrade():
    op.drop_index("ix_user_actions_owner", "user_actions")
    op.drop_table("auth_attempts")
    op.drop_table("account_sessions")
    op.drop_table("accounts")
