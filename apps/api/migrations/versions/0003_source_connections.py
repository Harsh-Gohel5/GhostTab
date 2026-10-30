"""Separate provider grants and selected-source provenance from Calendar."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "source_connections",
        sa.Column("owner_id", sa.String(100), primary_key=True),
        sa.Column("provider", sa.String(30), primary_key=True),
        sa.Column("grant_id", sa.String(36), nullable=False),
        sa.Column("encrypted_tokens", sa.Text(), nullable=False),
    )
    op.create_table(
        "source_oauth_states",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("owner_id", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("encrypted_verifier", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Float(), nullable=False),
    )
    op.create_table(
        "source_references",
        sa.Column("evidence_id", sa.String(36), sa.ForeignKey("evidence.id"), primary_key=True),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("external_id", sa.String(256), nullable=False),
        sa.Column("grant_id", sa.String(36), nullable=False),
    )
    if op.get_bind().dialect.name == "postgresql":
        for table in ("source_connections", "source_oauth_states", "source_references"):
            op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'REVOKE ALL ON TABLE "{table}" FROM PUBLIC')
            for role in ("anon", "authenticated"):
                op.execute(
                    sa.text(f"""DO $$ BEGIN
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                        REVOKE ALL ON TABLE "{table}" FROM "{role}";
                    END IF;
                END $$""")
                )


def downgrade():
    for table in ("source_references", "source_oauth_states", "source_connections"):
        op.drop_table(table)
