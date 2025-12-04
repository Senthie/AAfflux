"""
Author: Senthie seemoon2077@gmail.com
Date: 2025-12-04 01:28:03
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2025-12-04 02:30:56
FilePath: /api/app/utils/password.py
Description: 密码哈希和验证

Copyright (c) 2025 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

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
