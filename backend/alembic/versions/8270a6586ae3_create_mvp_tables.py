from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '8270a6586ae3'
down_revision: str | None = '0001_create_users'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('ai_cache',
    sa.Column('cache_key', sa.String(length=200), nullable=False),
    sa.Column('value_text', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('cache_key')
    )
    op.create_table('content',
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('creator_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('content_type', sa.String(length=64), nullable=False),
    sa.Column('duration_seconds', sa.Integer(), nullable=False),
    sa.Column('resolution', sa.String(length=32), nullable=False),
    sa.Column('bitrate_tier', sa.String(length=32), nullable=False),
    sa.Column('engagement_intent', sa.String(length=64), nullable=False),
    sa.Column('quality_score', sa.Integer(), nullable=False),
    sa.Column('suggested_price_per_second', sa.BigInteger(), nullable=False),
    sa.Column('price_per_second', sa.BigInteger(), nullable=False),
    sa.Column('ipfs_cid', sa.String(length=128), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_creator_id'), 'content', ['creator_id'], unique=False)
    op.create_table('creator_policies',
    sa.Column('creator_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('min_price_per_second', sa.BigInteger(), nullable=False),
    sa.Column('max_price_per_second', sa.BigInteger(), nullable=False),
    sa.Column('bulk_tiers_json', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('creator_id')
    )
    op.create_table('payment_channels',
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('content_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('price_per_second_locked', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.String(length=16), server_default=sa.text("'active'"), nullable=False),
    sa.Column('total_seconds_streamed', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('total_amount_owed', sa.BigInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('total_amount_settled', sa.BigInteger(), server_default=sa.text('0'), nullable=False),
    sa.Column('last_tick_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_settlement_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('opened_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['content_id'], ['content.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_channels_content_id'), 'payment_channels', ['content_id'], unique=False)
    op.create_index(op.f('ix_payment_channels_user_id'), 'payment_channels', ['user_id'], unique=False)
    op.create_table('settlements',
    sa.Column('id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('channel_id', sa.UUID(as_uuid=False), nullable=False),
    sa.Column('amount', sa.BigInteger(), nullable=False),
    sa.Column('tx_hash', sa.String(length=128), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['channel_id'], ['payment_channels.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settlements_channel_id'), 'settlements', ['channel_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_settlements_channel_id'), table_name='settlements')
    op.drop_table('settlements')
    op.drop_index(op.f('ix_payment_channels_user_id'), table_name='payment_channels')
    op.drop_index(op.f('ix_payment_channels_content_id'), table_name='payment_channels')
    op.drop_table('payment_channels')
    op.drop_table('creator_policies')
    op.drop_index(op.f('ix_content_creator_id'), table_name='content')
    op.drop_table('content')
    op.drop_table('ai_cache')
