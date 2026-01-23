"""create stream credits

Revision ID: b1f0c9c4a8c7
Revises: 8270a6586ae3
Create Date: 2026-01-23

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1f0c9c4a8c7"
down_revision = "8270a6586ae3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stream_credits",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("content_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("seconds_remaining", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "content_id", name="uq_stream_credits_user_content"),
    )
    op.create_index(op.f("ix_stream_credits_content_id"), "stream_credits", ["content_id"], unique=False)
    op.create_index(op.f("ix_stream_credits_user_id"), "stream_credits", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_stream_credits_user_id"), table_name="stream_credits")
    op.drop_index(op.f("ix_stream_credits_content_id"), table_name="stream_credits")
    op.drop_table("stream_credits")
