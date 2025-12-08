"""Initial migration with all models

Revision ID: 0dfdc9a62656
Revises:
Create Date: 2025-12-01 09:47:02.031283

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dfdc9a62656'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user table
    op.create_table(
        'user',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)

    # Create organization table
    op.create_table(
        'organization',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['user.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create team table
    op.create_table(
        'team',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['user.id'],
        ),
        sa.ForeignKeyConstraint(
            ['organization_id'],
            ['organization.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create teammember table
    op.create_table(
        'teammember',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['team_id'],
            ['team.id'],
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create workspace table
    op.create_table(
        'workspace',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('team_id', sa.UUID(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['user.id'],
        ),
        sa.ForeignKeyConstraint(
            ['team_id'],
            ['team.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_workspace_team_id'), 'workspace', ['team_id'], unique=False)

    # Create workflow table
    op.create_table(
        'workflow',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('input_schema', sa.JSON(), nullable=False),
        sa.Column('output_schema', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['workspace.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_workflow_workspace_id'), 'workflow', ['workspace_id'], unique=False)

    # Create node table
    op.create_table(
        'node',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('position', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ['workflow_id'],
            ['workflow.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_node_workflow_id'), 'node', ['workflow_id'], unique=False)

    # Create connection table
    op.create_table(
        'connection',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('source_node_id', sa.UUID(), nullable=False),
        sa.Column('target_node_id', sa.UUID(), nullable=False),
        sa.Column('source_output', sa.String(), nullable=False),
        sa.Column('target_input', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ['source_node_id'],
            ['node.id'],
        ),
        sa.ForeignKeyConstraint(
            ['target_node_id'],
            ['node.id'],
        ),
        sa.ForeignKeyConstraint(
            ['workflow_id'],
            ['workflow.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_connection_workflow_id'), 'connection', ['workflow_id'], unique=False)

    # Create executionrecord table
    op.create_table(
        'executionrecord',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('inputs', sa.JSON(), nullable=False),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['workflow_id'],
            ['workflow.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_executionrecord_workflow_id'), 'executionrecord', ['workflow_id'], unique=False
    )

    # Create nodeexecutionresult table
    op.create_table(
        'nodeexecutionresult',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('execution_record_id', sa.UUID(), nullable=False),
        sa.Column('node_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('inputs', sa.JSON(), nullable=False),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['execution_record_id'],
            ['executionrecord.id'],
        ),
        sa.ForeignKeyConstraint(
            ['node_id'],
            ['node.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_nodeexecutionresult_execution_record_id'),
        'nodeexecutionresult',
        ['execution_record_id'],
        unique=False,
    )

    # Create prompttemplate table
    op.create_table(
        'prompttemplate',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['user.id'],
        ),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['workspace.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_prompttemplate_workspace_id'), 'prompttemplate', ['workspace_id'], unique=False
    )

    # Create prompttemplateversion table
    op.create_table(
        'prompttemplateversion',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['template_id'],
            ['prompttemplate.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_prompttemplateversion_template_id'),
        'prompttemplateversion',
        ['template_id'],
        unique=False,
    )

    # Create llmprovider table
    op.create_table(
        'llmprovider',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('provider_type', sa.String(), nullable=False),
        sa.Column('api_key_encrypted', sa.String(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['user.id'],
        ),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['workspace.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_llmprovider_workspace_id'), 'llmprovider', ['workspace_id'], unique=False
    )

    # Create application table
    op.create_table(
        'application',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('api_key_hash', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['user.id'],
        ),
        sa.ForeignKeyConstraint(
            ['workflow_id'],
            ['workflow.id'],
        ),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['workspace.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_application_workspace_id'), 'application', ['workspace_id'], unique=False
    )

    # Create filereference table
    op.create_table(
        'filereference',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_type', sa.String(), nullable=False),
        sa.Column('uploaded_by', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['uploaded_by'],
            ['user.id'],
        ),
        sa.ForeignKeyConstraint(
            ['workspace_id'],
            ['workspace.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_filereference_file_id'), 'filereference', ['file_id'], unique=True)
    op.create_index(
        op.f('ix_filereference_workspace_id'), 'filereference', ['workspace_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table('filereference')
    op.drop_table('application')
    op.drop_table('llmprovider')
    op.drop_table('prompttemplateversion')
    op.drop_table('prompttemplate')
    op.drop_table('nodeexecutionresult')
    op.drop_table('executionrecord')
    op.drop_table('connection')
    op.drop_table('node')
    op.drop_table('workflow')
    op.drop_table('workspace')
    op.drop_table('teammember')
    op.drop_table('team')
    op.drop_table('organization')
    op.drop_table('user')
