"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/app/services/email_service.py
Description: 邮件服务

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务"""

    def __init__(self):
        self.smtp_server = getattr(settings, 'smtp_server', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'smtp_port', 587)
        self.smtp_username = getattr(settings, 'smtp_username', '')
        self.smtp_password = getattr(settings, 'smtp_password', '')
        self.from_email = getattr(settings, 'from_email', 'noreply@yourapp.com')

    async def send_invitation_email(
        self, to_email: str, inviter_name: str, team_name: str, invite_token: str, expires_at: str
    ) -> bool:
        """发送邀请邮件"""
        try:
            # 构建邀请链接
            frontend_url = getattr(settings, 'frontend_url', 'https://yourapp.com')
            invite_link = f'{frontend_url}/accept-invitation?token={invite_token}'

            # 创建邮件内容
            subject = f'您被邀请加入 {team_name} 团队'
            html_content = self._create_invitation_html(
                inviter_name, team_name, invite_link, expires_at
            )

            # 发送邮件
            return self._send_email(to_email, subject, html_content)

        except Exception as e:
            logger.error(f'发送邀请邮件失败: {e}')
            return False

    def _create_invitation_html(
        self, inviter_name: str, team_name: str, invite_link: str, expires_at: str
    ) -> str:
        """创建邀请邮件HTML模板"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>团队邀请</title>
            <style>
                .container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .button {{
                    display: inline-block;
                    background: #4F46E5;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>团队邀请</h1>
                </div>
                <div class="content">
                    <h2>您好！</h2>
                    <p><strong>{inviter_name}</strong> 邀请您加入 <strong>{team_name}</strong> 团队。</p>
                    <p>点击下面的按钮接受邀请：</p>
                    <a href="{invite_link}" class="button">接受邀请</a>
                    <p>或复制以下链接到浏览器：</p>
                    <p style="word-break: break-all; background: #fff; padding: 10px; border: 1px solid #ddd;">
                        {invite_link}
                    </p>
                    <p><strong>注意：</strong>此邀请将在 {expires_at} 过期。</p>
                </div>
                <div class="footer">
                    <p>如果您没有请求此邀请，请忽略此邮件。</p>
                    <p>© 2024 您的应用名称</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送邮件"""
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 使用和成功测试相同的逻辑
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f'邮件发送成功: {to_email}')
            return True

        except Exception as e:
            logger.error(f'SMTP发送失败: {e}')
            return False
