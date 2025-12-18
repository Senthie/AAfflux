"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-10 11:51:36
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-15 09:47:02
FilePath: : AAfflux: api: tests: test_file_storage.py
Description:文件存储功能测试脚本
"""

import asyncio
from io import BytesIO
from uuid import uuid4

from app.core.database import get_session
from app.services.file_server import FileService


async def test_file_storage():
    """测试文件存储功能"""

    # 初始化 MongoDB 连接
    from app.core.mongodb import mongodb_client

    await mongodb_client.connect()
    print('MongoDB connected successfully!')

    # 创建测试文件
    test_content = b'Hello, this is a test file!'

    # 创建一个简单的测试文件对象
    class TestUploadFile:
        def __init__(self, content: bytes, filename: str, content_type: str):
            self.file = BytesIO(content)
            self.filename = filename
            self.content_type = content_type
            self.size = len(content)

        async def seek(self, position: int):
            self.file.seek(position)

        async def read(self, size: int = -1):
            return self.file.read(size)

    test_file = TestUploadFile(test_content, 'test.txt', 'text/plain')

    # 获取数据库会话
    session_gen = get_session()
    session = await anext(session_gen)

    try:
        # 创建文件服务
        file_service = FileService(session)

        # 测试上传
        print('Testing file upload...')
        file_ref = await file_service.upload_file(
            file=test_file, workspace_id=uuid4(), uploaded_by=uuid4()
        )
        print(f'Upload successful: {file_ref.file_id}')

        # 测试下载
        print('Testing file download...')
        downloaded_ref, file_stream = await file_service.download_file(file_ref.file_id)

        # 读取内容
        content = b''
        async for chunk in file_stream:
            content += chunk
        assert content == test_content
        print('Download successful and content matches!')

        # 测试删除
        print('Testing file deletion...')
        success = await file_service.delete_file(file_ref.file_id)
        assert success
        print('Deletion successful!')

        print('All tests passed! ✅')

    except Exception as e:
        print(f'Test failed: {e}')
    finally:
        await session_gen.aclose()
        # 关闭 MongoDB 连接
        await mongodb_client.close()
        print('MongoDB connection closed.')


if __name__ == '__main__':
    asyncio.run(test_file_storage())
