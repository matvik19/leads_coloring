"""Create initial tables

Revision ID: 001_initial
Revises:
Create Date: 2024-12-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subdomain_settings table
    op.create_table(
        'subdomain_settings',
        sa.Column('subdomain', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=False, server_default='Europe/Moscow'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('subdomain')
    )
    op.create_index(op.f('ix_subdomain_settings_subdomain'), 'subdomain_settings', ['subdomain'], unique=False)

    # Create coloring_rules table
    op.create_table(
        'coloring_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subdomain', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conditions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('style', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_coloring_rules_subdomain'), 'coloring_rules', ['subdomain'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_coloring_rules_subdomain'), table_name='coloring_rules')
    op.drop_table('coloring_rules')
    op.drop_index(op.f('ix_subdomain_settings_subdomain'), table_name='subdomain_settings')
    op.drop_table('subdomain_settings')
