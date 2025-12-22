"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-22 10:27:08
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-22 15:00:47
FilePath: : AAfflux: api: app: utils: api_key.py
Description:api密钥生成和验证
"""

import secrets
import hashlib
import hmac
from typing import Optional, Tuple
from datetime import datetime, timedelta


class APIKeyGenerator:
    """API密钥生成器"""

    @staticmethod
    def generate_api_key(prefix: str = "ak") -> str:
        """生成API密钥

        Args:
            prefix: 密钥前缀，默认为"ak"

        Returns:
            生成的API密钥
        """
        # 生成32字节的随机数据
        random_bytes = secrets.token_bytes(32)
        # 转换为十六进制字符串
        key_suffix = random_bytes.hex()
        # 添加前缀
        return f"{prefix}_{key_suffix}"

    @staticmethod
    def generate_secret_key() -> str:
        """生成密钥对应的密钥

        Returns:
            生成的密钥
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_api_key(api_key: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """对API密钥进行哈希处理

        Args:
            api_key: 原始API密钥
            salt: 盐值，如果不提供则自动生成

        Returns:
            (哈希值, 盐值)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        # 使用PBKDF2进行哈希
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            api_key.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        )

        return hashed.hex(), salt

    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str, salt: str) -> bool:
        """验证API密钥

        Args:
            api_key: 原始API密钥
            hashed_key: 存储的哈希值
            salt: 盐值

        Returns:
            验证结果
        """
        try:
            # 重新计算哈希
            computed_hash, _ = APIKeyGenerator.hash_api_key(api_key, salt)
            # 使用安全的比较方法
            return hmac.compare_digest(computed_hash, hashed_key)
        except Exception:
            return False


class APIKeyValidator:
    """API密钥验证器"""

    @staticmethod
    def validate_key_format(api_key: str) -> bool:
        """验证API密钥格式

        Args:
            api_key: API密钥

        Returns:
            格式是否正确
        """
        if not api_key:
            return False

        # 检查是否包含前缀
        if '_' not in api_key:
            return False

        prefix, key_part = api_key.split('_', 1)

        # 检查前缀长度
        if len(prefix) < 2 or len(prefix) > 10:
            return False

        # 检查密钥部分长度（64个十六进制字符）
        if len(key_part) != 64:
            return False

        # 检查是否为有效的十六进制字符串
        try:
            int(key_part, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_expired(created_at: datetime, expires_in_days: Optional[int] = None) -> bool:
        """检查API密钥是否过期

        Args:
            created_at: 创建时间
            expires_in_days: 过期天数，None表示永不过期

        Returns:
            是否过期
        """
        if expires_in_days is None:
            return False

        expiry_date = created_at + timedelta(days=expires_in_days)
        return datetime.utcnow() > expiry_date


class APIKeyManager:
    """API密钥管理器"""

    def __init__(self):
        self.generator = APIKeyGenerator()
        self.validator = APIKeyValidator()

    def create_api_key(
        self,
        name: str,
        prefix: str = "ak",
        expires_in_days: Optional[int] = None
    ) -> dict:
        """创建API密钥

        Args:
            name: 密钥名称
            prefix: 密钥前缀
            expires_in_days: 过期天数

        Returns:
            包含密钥信息的字典
        """
        # 生成API密钥
        api_key = self.generator.generate_api_key(prefix)

        # 生成哈希和盐
        hashed_key, salt = self.generator.hash_api_key(api_key)

        # 计算过期时间
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        return {
            "api_key": api_key,  # 只在创建时返回，不存储
            "hashed_key": hashed_key,  # 存储到数据库
            "salt": salt,  # 存储到数据库
            "name": name,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "is_active": True
        }

    def verify_api_key(
        self,
        api_key: str,
        hashed_key: str,
        salt: str,
        created_at: datetime,
        expires_in_days: Optional[int] = None,
        is_active: bool = True
    ) -> bool:
        """验证API密钥

        Args:
            api_key: 原始API密钥
            hashed_key: 存储的哈希值
            salt: 盐值
            created_at: 创建时间
            expires_in_days: 过期天数
            is_active: 是否激活

        Returns:
            验证结果
        """
        # 检查是否激活
        if not is_active:
            return False

        # 检查格式
        if not self.validator.validate_key_format(api_key):
            return False

        # 检查是否过期
        if self.validator.is_expired(created_at, expires_in_days):
            return False

        # 验证密钥
        return self.generator.verify_api_key(api_key, hashed_key, salt)

    def revoke_api_key(self, api_key_id: str) -> bool:
        """撤销API密钥

        Args:
            api_key_id: API密钥ID

        Returns:
            撤销结果
        """
        # 这里应该更新数据库中的is_active字段为False
        # 具体实现在service层
        pass
