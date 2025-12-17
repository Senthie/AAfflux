"""邀请安全管理器"""

import hmac
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID

from app.core.config import settings
from app.core.redis import RedisClient


class InvitationSecurityManager:
    """邀请安全管理器"""

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client
        self.config = settings.invitation_security

    async def check_rate_limit(self, user_id: UUID) -> Dict[str, Any]:
        """检查用户邀请频率限制"""
        now = datetime.utcnow()

        # 检查小时限制
        hour_key = f'invite_rate:{user_id}:hour:{now.strftime("%Y%m%d%H")}'
        hour_count = int(await self.redis.get(hour_key) or 0)

        # 检查日限制
        day_key = f'invite_rate:{user_id}:day:{now.strftime("%Y%m%d")}'
        day_count = int(await self.redis.get(day_key) or 0)

        # 检查月限制
        month_key = f'invite_rate:{user_id}:month:{now.strftime("%Y%m")}'
        month_count = int(await self.redis.get(month_key) or 0)

        # 检查是否超限
        if hour_count >= self.config.rate_limit_hour:
            return {
                'allowed': False,
                'reason': f'每小时最多发送{self.config.rate_limit_hour}个邀请',
                'reset_time': (now + timedelta(hours=1)).replace(minute=0, second=0),
                'current_count': hour_count,
                'limit': self.config.rate_limit_hour,
                'period': 'hour',
            }

        if day_count >= self.config.rate_limit_day:
            return {
                'allowed': False,
                'reason': f'每天最多发送{self.config.rate_limit_day}个邀请',
                'reset_time': (now + timedelta(days=1)).replace(hour=0, minute=0, second=0),
                'current_count': day_count,
                'limit': self.config.rate_limit_day,
                'period': 'day',
            }

        if month_count >= self.config.rate_limit_month:
            return {
                'allowed': False,
                'reason': f'每月最多发送{self.config.rate_limit_month}个邀请',
                'reset_time': (now.replace(day=1) + timedelta(days=32)).replace(
                    day=1, hour=0, minute=0, second=0
                ),
                'current_count': month_count,
                'limit': self.config.rate_limit_month,
                'period': 'month',
            }

        return {
            'allowed': True,
            'hour_count': hour_count,
            'day_count': day_count,
            'month_count': month_count,
        }

    async def increment_rate_limit(self, user_id: UUID):
        """增加用户邀请计数"""
        now = datetime.utcnow()

        # 增加小时计数
        hour_key = f'invite_rate:{user_id}:hour:{now.strftime("%Y%m%d%H")}'
        await self.redis.incr(hour_key)
        await self.redis.expire(hour_key, 3600)  # 1小时过期

        # 增加日计数
        day_key = f'invite_rate:{user_id}:day:{now.strftime("%Y%m%d")}'
        await self.redis.incr(day_key)
        await self.redis.expire(day_key, 86400)  # 24小时过期

        # 增加月计数
        month_key = f'invite_rate:{user_id}:month:{now.strftime("%Y%m")}'
        await self.redis.incr(month_key)
        await self.redis.expire(month_key, 2678400)  # 31天过期

    def generate_secure_token(self, team_id: UUID, email: str) -> str:
        """生成安全令牌"""
        # 生成基础随机令牌
        base_token = secrets.token_urlsafe(self.config.token_length)

        # 生成HMAC签名
        timestamp = str(int(datetime.utcnow().timestamp()))
        message = f'{team_id}:{email}:{base_token}:{timestamp}'
        signature = hmac.new(
            settings.secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()[:16]  # 取前16位

        # 组合最终令牌: base_token.timestamp.signature
        secure_token = f'{base_token}.{timestamp}.{signature}'
        return secure_token

    def verify_token_signature(self, token: str, team_id: UUID, email: str) -> bool:
        """验证令牌签名"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False

            base_token, timestamp, signature = parts

            # 重新计算签名
            message = f'{team_id}:{email}:{base_token}:{timestamp}'
            expected_signature = hmac.new(
                settings.secret_key.encode(), message.encode(), hashlib.sha256
            ).hexdigest()[:16]

            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

    async def check_token_usage(self, token: str) -> Dict[str, Any]:
        """检查令牌使用情况"""
        usage_key = f'token_usage:{token}'
        usage_data = await self.redis.get(usage_key)

        if not usage_data:
            return {'used': False, 'attempts': 0}

        usage_info = json.loads(usage_data)
        return usage_info

    async def record_token_attempt(
        self, token: str, success: bool = False, user_id: UUID = None
    ) -> bool:
        """记录令牌使用尝试"""
        usage_key = f'token_usage:{token}'
        usage_data = await self.redis.get(usage_key)

        if usage_data:
            usage_info = json.loads(usage_data)
        else:
            usage_info = {
                'used': False,
                'attempts': 0,
                'first_attempt': datetime.utcnow().isoformat(),
            }

        usage_info['attempts'] += 1
        usage_info['last_attempt'] = datetime.utcnow().isoformat()

        if success:
            usage_info['used'] = True
            usage_info['used_by'] = str(user_id) if user_id else None
            usage_info['used_at'] = datetime.utcnow().isoformat()

        # 如果尝试次数过多，标记为可疑
        if usage_info['attempts'] > self.config.max_token_attempts:
            usage_info['suspicious'] = True
            # 将令牌加入黑名单
            blocked_key = f'blocked_tokens:{token}'
            await self.redis.setex(blocked_key, 86400, '1')  # 24小时黑名单

        # 保存使用信息，7天过期
        await self.redis.setex(usage_key, 604800, json.dumps(usage_info))

        return usage_info.get('suspicious', False)
