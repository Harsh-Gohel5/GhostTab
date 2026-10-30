"""Persist human review and completion independently from source generations."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("reviewed_snapshot_id", sa.String(36), nullable=True))
    op.add_column("tasks", sa.Column("reviewed_at", sa.Float(), nullable=True))
    op.add_column("tasks", sa.Column("completed_at", sa.Float(), nullable=True))
    op.add_column("tasks", sa.Column("completed_generation", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("tasks") as batch:
        for name in ("completed_generation", "completed_at", "reviewed_at", "reviewed_snapshot_id"):
            batch.drop_column(name)
