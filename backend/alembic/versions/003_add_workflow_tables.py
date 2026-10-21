"""Add workflow, version, execution, node_execution, scheduled_job tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'published', 'paused', 'archived', name='workflow_status', native_enum=False), nullable=False, default='draft'),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('is_template', sa.Boolean(), nullable=False, default=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflow_org_status', 'workflows', ['organization_id', 'status'])
    op.create_index('ix_workflow_org_created', 'workflows', ['organization_id', 'created_at'])
    op.create_index('ix_workflows_organization_id', 'workflows', ['organization_id'])

    # Create workflow_versions table
    op.create_table(
        'workflow_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('nodes', sa.JSON(), nullable=False, default=list),
        sa.Column('edges', sa.JSON(), nullable=False, default=list),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'version', name='uq_workflow_version'),
    )
    op.create_index('ix_workflow_version_workflow', 'workflow_versions', ['workflow_id', 'version'])
    op.create_index('ix_workflow_versions_workflow_id', 'workflow_versions', ['workflow_id'])

    # Create workflow_executions table
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', 'paused', name='workflow_execution_status', native_enum=False), nullable=False, default='pending'),
        sa.Column('trigger_type', sa.String(length=100), nullable=True),
        sa.Column('trigger_data', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('parent_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_execution_id'], ['workflow_executions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['version_id'], ['workflow_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_execution_idempotency', 'workflow_executions', ['idempotency_key'])
    op.create_index('ix_execution_org_status', 'workflow_executions', ['organization_id', 'status'])
    op.create_index('ix_execution_workflow', 'workflow_executions', ['workflow_id', 'started_at'])
    op.create_index('ix_workflow_executions_idempotency_key', 'workflow_executions', ['idempotency_key'])
    op.create_index('ix_workflow_executions_organization_id', 'workflow_executions', ['organization_id'])
    op.create_index('ix_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'])

    # Create node_executions table
    op.create_table(
        'node_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', sa.String(length=100), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'skipped', 'retrying', name='node_execution_status', native_enum=False), nullable=False, default='pending'),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_node_execution_exec_node', 'node_executions', ['execution_id', 'node_id'])
    op.create_index('ix_node_execution_status', 'node_executions', ['status'])
    op.create_index('ix_node_executions_execution_id', 'node_executions', ['execution_id'])
    op.create_index('ix_node_executions_node_id', 'node_executions', ['node_id'])

    # Create scheduled_jobs table
    op.create_table(
        'scheduled_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=True),
        sa.Column('run_once_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, default='UTC'),
        sa.Column('trigger_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='scheduled_job_status', native_enum=False), nullable=False, default='pending'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_runs', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scheduled_job_next_run', 'scheduled_jobs', ['next_run_at'])
    op.create_index('ix_scheduled_job_org_active', 'scheduled_jobs', ['organization_id', 'is_active'])
    op.create_index('ix_scheduled_jobs_next_run_at', 'scheduled_jobs', ['next_run_at'])
    op.create_index('ix_scheduled_jobs_organization_id', 'scheduled_jobs', ['organization_id'])
    op.create_index('ix_scheduled_jobs_workflow_id', 'scheduled_jobs', ['workflow_id'])


def downgrade() -> None:
    op.drop_constraint('uq_contacts_org_phone_number', 'contacts', type_='unique')
    op.drop_table('scheduled_jobs')
    op.drop_table('node_executions')
    op.drop_table('workflow_executions')
    op.drop_table('workflow_versions')
    op.drop_table('workflows')

    op.execute('DROP TYPE IF EXISTS workflow_status')
    op.execute('DROP TYPE IF EXISTS workflow_execution_status')
    op.execute('DROP TYPE IF EXISTS node_execution_status')
    op.execute('DROP TYPE IF EXISTS scheduled_job_status')