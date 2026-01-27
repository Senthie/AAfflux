"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/tests/services/test_file_service.py
Description: Test File Service服务

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

"""
文件服务层测试

来自: test_file_storage.py

测试内容:
- 文件上传
- 文件下载
- 文件删除
"""

from io import BytesIO
from uuid import uuid4

import pytest


class TestUploadFile:
    """测试文件上传对象"""

    def __init__(self, content: bytes, filename: str, content_type: str):
        self.file = BytesIO(content)
        self.filename = filename
        self.content_type = content_type
        self.size = len(content)

    async def seek(self, position: int):
        self.file.seek(position)

    async def read(self, size: int = -1):
        return self.file.read(size)


@pytest.mark.asyncio
async def test_file_storage():
    """测试文件存储功能"""
    from app.core.database import get_session
    from app.core.mongodb import mongodb_client
    from app.services.file_server import FileService

    await mongodb_client.connect()

    test_content = b'Hello, this is a test file!'
    test_file = TestUploadFile(test_content, 'test.txt', 'text/plain')

    session_gen = get_session()
    session = await anext(session_gen)

    try:
        file_service = FileService(session)

        # 测试上传
        file_ref = await file_service.upload_file(
            file=test_file, workspace_id=uuid4(), uploaded_by=uuid4()
        )
        assert file_ref.file_id is not None

        # 测试下载
        downloaded_ref, file_stream = await file_service.download_file(file_ref.file_id)
        content = b''
        async for chunk in file_stream:
            content += chunk
        assert content == test_content

        # 测试删除
        success = await file_service.delete_file(file_ref.file_id)
        assert success

    except Exception as e:
        pytest.fail(f'Test failed: {e}')
    finally:
        await session_gen.aclose()
        await mongodb_client.close()
