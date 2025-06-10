"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-06-10
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String, unique=True, index=True),
        sa.Column('password_hash', sa.String),
        sa.Column('role', sa.String),
        sa.Column('is_active', sa.Boolean, default=True),
    )
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String),
        sa.Column('client_name', sa.String),
    )
    op.create_table(
        'batches',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id')),
        sa.Column('reception_date', sa.DateTime),
        sa.Column('due_date', sa.DateTime),
        sa.Column('initial_volume', sa.Integer),
        sa.Column('status', sa.String, default='Received'),
    )
    op.create_table(
        'performance_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
        sa.Column('batch_id', sa.Integer, sa.ForeignKey('batches.id')),
        sa.Column('start_time', sa.DateTime),
        sa.Column('end_time', sa.DateTime, nullable=True),
        sa.Column('items_processed', sa.Integer),
    )


def downgrade():
    op.drop_table('performance_logs')
    op.drop_table('batches')
    op.drop_table('projects')
    op.drop_table('users')
