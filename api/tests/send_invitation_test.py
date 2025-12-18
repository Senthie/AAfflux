"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-17 16:58:27
LastEditors: kk123047 3254834740@qq.com
LastEditTime: 2025-12-18 09:09:29
FilePath: : AAfflux: api: tests: send_invitation_test.py
Description:邮箱发送
"""
#!/usr/bin/env python3
"""
测试邀请邮件发送服务
发送邀请邮件到 handstrip01@handscript.net
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import EmailService


async def test_send_invitation():
    """测试发送邀请邮件"""

    # 创建邮件服务实例
    email_service = EmailService()

    # 邮件参数
    to_email = "jhonkon@handscript.net"
    inviter_name = "系统管理员"
    team_name = "测试团队"
    invite_token = "test_token_123456789"
    expires_at = (datetime.now() + timedelta(days=7)).strftime('%Y年%m月%d日 %H:%M')

    print(f"正在发送邀请邮件到: {to_email}")
    print(f"邀请者: {inviter_name}")
    print(f"团队名称: {team_name}")
    print(f"过期时间: {expires_at}")
    print("-" * 50)

    try:
        # 发送邮件
        success = await email_service.send_invitation_email(
            to_email=to_email,
            inviter_name=inviter_name,
            team_name=team_name,
            invite_token=invite_token,
            expires_at=expires_at
        )

        if success:
            print("✅ 邮件发送成功！")
            print(f"邀请邮件已发送到 {to_email}")
        else:
            print("❌ 邮件发送失败！")
            print("请检查SMTP配置和网络连接")

    except Exception as e:
        print(f"❌ 发送邮件时出现错误: {e}")
        import traceback
        traceback.print_exc()


async def test_email_config():
    """测试邮件配置"""

    print("检查邮件配置...")
    print("-" * 30)

    email_service = EmailService()

    print(f"SMTP服务器: {email_service.smtp_server}")
    print(f"SMTP端口: {email_service.smtp_port}")
    print(f"SMTP用户名: {email_service.smtp_username}")
    print(f"发件人邮箱: {email_service.from_email}")
    print(f"SMTP密码: {'已配置' if email_service.smtp_password else '未配置'}")
    print("-" * 30)


if __name__ == "__main__":
    print("🚀 启动邀请邮件发送测试")
    print("=" * 50)

    # 运行测试
    asyncio.run(test_email_config())
    print()
    asyncio.run(test_send_invitation())
