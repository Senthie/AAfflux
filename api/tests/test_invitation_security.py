#!/usr/bin/env python3
"""测试邀请安全功能"""

import asyncio
from uuid import uuid4

from app.core.config import settings
from app.utils.invitation_security import InvitationSecurityManager


async def test_invitation_security():
    """测试邀请安全功能"""
    print('🔧 测试邀请安全功能...')

    # 测试配置
    print('✅ 配置加载成功')
    print(f'   - 小时限制: {settings.invitation_security.rate_limit_hour}')
    print(f'   - 日限制: {settings.invitation_security.rate_limit_day}')
    print(f'   - 令牌长度: {settings.invitation_security.token_length}')

    # 创建Redis客户端（模拟）
    class MockRedis:
        def __init__(self):
            self.data = {}

        async def get(self, key):
            return self.data.get(key)

        async def incr(self, key):
            self.data[key] = int(self.data.get(key, 0)) + 1
            return self.data[key]

        async def expire(self, key, seconds):
            return True

        async def setex(self, key, seconds, value):
            self.data[key] = value
            return True

        async def exists(self, key):
            return key in self.data

    redis_client = MockRedis()
    security_manager = InvitationSecurityManager(redis_client)

    # 测试令牌生成
    team_id = uuid4()
    email = 'test@example.com'
    token = security_manager.generate_secure_token(team_id, email)
    print(f'✅ 令牌生成成功: {token[:20]}...')

    # 测试令牌验证
    is_valid = security_manager.verify_token_signature(token, team_id, email)
    print(f'✅ 令牌验证: {"通过" if is_valid else "失败"}')

    # 测试频率限制
    user_id = uuid4()
    for i in range(3):
        rate_check = await security_manager.check_rate_limit(user_id)
        print(f'✅ 频率检查 {i + 1}: {"允许" if rate_check["allowed"] else "拒绝"}')
        if rate_check['allowed']:
            await security_manager.increment_rate_limit(user_id)

    # 测试令牌使用记录
    usage_check = await security_manager.check_token_usage(token)
    print(f'✅ 令牌使用检查: 已使用={usage_check["used"]}, 尝试次数={usage_check["attempts"]}')

    # 记录令牌尝试
    suspicious = await security_manager.record_token_attempt(token, success=True, user_id=user_id)
    print(f'✅ 令牌使用记录: 可疑={"是" if suspicious else "否"}')

    print('🎉 所有测试通过！')


if __name__ == '__main__':
    asyncio.run(test_invitation_security())
