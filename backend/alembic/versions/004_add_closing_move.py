"""Revision ID: 004
Revises: 003
Create Date: 2026-07-31

Adds the skills-gap field: the single highest-leverage action that would make
the candidate credible for a given role.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("job_matches", sa.Column("closing_move", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_matches", "closing_move")
