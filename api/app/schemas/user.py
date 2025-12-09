"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-05 17:49:41
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-09 17:50:51
FilePath: : AAfflux: api: app: schemas: user.py
Description:用户相关schemas
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserProfileResponse(BaseModel):
    """用户资料响应"""

    id: UUID = Field(..., description='用户唯一标识符')
    name: str = Field(..., description='用户姓名')
    email: EmailStr = Field(..., description='用户邮箱')
    avatar_url: Optional[str] = Field(None, description='头像URL')
    created_at: datetime = Field(..., description='创建时间')
    updated_at: datetime = Field(..., description='更新时间')

    class Config:
        from_attributes = True
        json_schema_extra = {
            'example': {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'name': '张三',
                'email': 'zhangsan@example.com',
                'avatar_url': 'https://example.com/avatars/user123.jpg',
                'created_at': '2025-12-05T10:30:00Z',
                'updated_at': '2025-12-05T10:30:00Z',
            }
        }


class UserUpdateRequest(BaseModel):
    """用户资料更新请求"""

    name: Optional[str] = Field(None, max_length=255, description='用户姓名')
    email: Optional[EmailStr] = Field(None, description='用户邮箱')

    class Config:
        json_schema_extra = {
            'example': {
                'name': '李四',
                'email': 'lisi@example.com',
            }
        }


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""

    old_password: str = Field(..., min_length=6, description='旧密码')
    new_password: str = Field(..., min_length=6, description='新密码')

    class Config:
        json_schema_extra = {
            'example': {
                'old_password': 'oldpass123',
                'new_password': 'newpass456',
            }
        }


class PasswordChangeResponse(BaseModel):
    """密码修改响应"""

    success: bool = Field(..., description='是否成功')
    message: str = Field(..., description='响应消息')

    class Config:
        json_schema_extra = {
            'example': {
                'success': True,
                'message': '密码修改成功',
            }
        }


class AvatarUploadResponse(BaseModel):
    """头像上传响应"""

    avatar_url: str = Field(..., description='头像URL')
    message: str = Field(..., description='响应消息')

    class Config:
        json_schema_extra = {
            'example': {
                'avatar_url': 'https://example.com/avatars/user123.jpg',
                'message': '头像上传成功',
            }
        }


class UserDeleteResponse(BaseModel):
    """用户删除响应"""

    success: bool = Field(..., description='是否成功')
    message: str = Field(..., description='响应消息')
    user_id: UUID = Field(..., description='被删除的用户ID')

    class Config:
        json_schema_extra = {
            'example': {
                'success': True,
                'message': '账号已删除',
                'user_id': '550e8400-e29b-41d4-a716-446655440000',
            }
        }
