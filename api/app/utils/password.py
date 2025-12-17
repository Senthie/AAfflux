"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 01:28:03
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-04 02:30:56
FilePath: /api/app/utils/password.py
Description: 密码哈希和验证，文本加密解密

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.hash import pbkdf2_sha256


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证用户传递进来的密码是否正确
    :param plain_password: 明文密码
    :param hashed_password: 密文密码
    :return: True or False
    """

    return pbkdf2_sha256.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码的哈希值
    :param password: 明文密码
    """
    return pbkdf2_sha256.hash(password)


def _get_encryption_key() -> bytes:
    """
    获取加密密钥，从环境变量或生成默认密钥
    """
    # 从环境变量获取密钥，如果不存在则使用默认值
    password = os.getenv('ENCRYPTION_KEY', 'default-encryption-key-change-in-production').encode()
    salt = os.getenv('ENCRYPTION_SALT', 'default-salt').encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return key


def encrypt_text(text: str) -> str:
    """
    加密文本

    Args:
        text: 要加密的明文

    Returns:
        str: 加密后的文本（Base64编码）
    """
    if not text:
        return text

    key = _get_encryption_key()
    f = Fernet(key)
    encrypted_bytes = f.encrypt(text.encode())
    return base64.urlsafe_b64encode(encrypted_bytes).decode()


def decrypt_text(encrypted_text: str) -> str:
    """
    解密文本

    Args:
        encrypted_text: 加密的文本（Base64编码）

    Returns:
        str: 解密后的明文
    """
    if not encrypted_text:
        return encrypted_text

    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
        decrypted_bytes = f.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    except Exception as e:
        raise ValueError(f'Failed to decrypt text: {e}')
