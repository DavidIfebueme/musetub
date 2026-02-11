"""add thumbnail_cid to content

Revision ID: c3d7e1f5a9b2
Revises: b1f0c9c4a8c7
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d7e1f5a9b2"
down_revision = "b1f0c9c4a8c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content", sa.Column("thumbnail_cid", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("content", "thumbnail_cid")
