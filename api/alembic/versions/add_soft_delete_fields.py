"""add soft delete fields to missing tables

Revision ID: add_soft_delete_001
Revises: 559fb8d7205a
Create Date: 2025-12-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_soft_delete_001'
down_revision: Union[str, None] = '559fb8d7205a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加软删除字段到需要的表"""
    
    # 需要添加软删除字段的表（排除不需要软删除的表）
    tables_need_soft_delete = [
        # BPM相关
        'bpm_form_definitions',
        
        # 对话相关
        'conversations',
        'messages',
        'end_users',
        
        # 数据集相关
        'documents',
        'document_segments',
        
        # 文件相关
        'file_references',
        
        # 插件相关
        'installed_plugins',
        
        # 工作流相关
        'nodes',
        
        # 提示词模板版本
        'prompt_template_versions',
    ]
    
    # 为每个表添加软删除字段
    for table_name in tables_need_soft_delete:
        # 添加 deleted_at 字段
        op.add_column(
            table_name,
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
        )
        
        # 添加 is_deleted 字段
        op.add_column(
            table_name,
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false')
        )
        
        # 为 deleted_at 创建索引（提高软删除查询性能）
        op.create_index(
            f'ix_{table_name}_deleted_at',
            table_name,
            ['deleted_at']
        )
        
        # 为 is_deleted 创建索引
        op.create_index(
            f'ix_{table_name}_is_deleted',
            table_name,
            ['is_deleted']
        )


def downgrade() -> None:
    """移除软删除字段"""
    
    tables_need_soft_delete = [
        'bpm_form_definitions',
        'conversations',
        'messages',
        'end_users',
        'documents',
        'document_segments',
        'file_references',
        'installed_plugins',
        'nodes',
        'prompt_template_versions',
    ]
    
    for table_name in tables_need_soft_delete:
        # 删除索引
        op.drop_index(f'ix_{table_name}_is_deleted', table_name=table_name)
        op.drop_index(f'ix_{table_name}_deleted_at', table_name=table_name)
        
        # 删除字段
        op.drop_column(table_name, 'is_deleted')
        op.drop_column(table_name, 'deleted_at')
