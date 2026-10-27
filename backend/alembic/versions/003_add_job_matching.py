"""Revision ID: 003
Revises: 002
Create Date: 2026-07-31

Adds the job matching agent tables: a candidate resume and one agent verdict
per (job, profile) pair.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("label", sa.Text(), nullable=False, server_default="default"),
        sa.Column("resume_text", sa.Text(), nullable=False),
        sa.Column("preferences", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_candidate_profiles_active",
        "candidate_profiles",
        ["is_active"],
        postgresql_where=sa.text("is_active"),
    )

    op.create_table(
        "job_matches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("profile_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("verdict", sa.Text(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column(
            "matched_skills",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "missing_skills",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "profile_id", name="uq_job_matches_job_profile"),
    )
    # Ranked-jobs view reads score-descending; the index keeps that ordered
    # scan off a sort of the whole table as verdict counts grow.
    op.create_index("ix_job_matches_score", "job_matches", [sa.text("score DESC")])
    op.create_index("ix_job_matches_profile", "job_matches", ["profile_id"])


def downgrade() -> None:
    op.drop_index("ix_job_matches_profile", table_name="job_matches")
    op.drop_index("ix_job_matches_score", table_name="job_matches")
    op.drop_table("job_matches")
    op.drop_index("ix_candidate_profiles_active", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")
