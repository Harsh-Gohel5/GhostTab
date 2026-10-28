"""Persist worker presence separately from job leases."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "worker_heartbeats",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("seen_at", sa.Float(), nullable=False),
    )
    op.create_index("ix_worker_heartbeats_seen_at", "worker_heartbeats", ["seen_at"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute('ALTER TABLE "worker_heartbeats" ENABLE ROW LEVEL SECURITY')
        op.execute('REVOKE ALL ON TABLE "worker_heartbeats" FROM PUBLIC')
        for role in ("anon", "authenticated"):
            op.execute(
                sa.text(f"""DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                    REVOKE ALL ON TABLE worker_heartbeats FROM "{role}";
                END IF;
            END $$""")
            )


def downgrade():
    op.drop_index("ix_worker_heartbeats_seen_at", table_name="worker_heartbeats")
    op.drop_table("worker_heartbeats")
