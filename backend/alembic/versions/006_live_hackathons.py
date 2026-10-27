"""Retire unverified seed listings; permit distinct editions on one website."""
from alembic import op
import sqlalchemy as sa
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    for constraint in sa.inspect(bind).get_unique_constraints("hackathons"):
        if constraint["column_names"] == ["url"]:
            op.drop_constraint(constraint["name"], "hackathons", type_="unique")
    op.execute("UPDATE hackathons SET status = 'unverified' WHERE source_name = 'static_list'")


def downgrade():
    # Multiple editions may now share a URL; deliberately retain their data.
    pass
