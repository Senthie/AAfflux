"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/models/file/__init__.py
Description: 模块初始化

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from app.models.file.reference import FileReference

__all__ = [
    'FileReference',
]


def get_file_service():
    """Lazy import file service to avoid config dependency."""
    from app.models.file.service import file_service

    return file_service
