"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:45:38
FilePath: /api/app/core/sentry.py
Description: Sentry错误监控配置

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from typing import Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings


def init_sentry() -> None:
    """Initialize Sentry error tracking."""
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[
                FastApiIntegration(transaction_style='endpoint'),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
            attach_stacktrace=True,
            before_send=before_send_filter,
        )


def before_send_filter(event: dict, hint: dict) -> Optional[dict]:
    """
    Filter events before sending to Sentry.

    Args:
        event: Sentry event
        hint: Additional context

    Returns:
        Modified event or None to drop
    """
    # Filter out health check errors
    if 'request' in event:
        url = event['request'].get('url', '')
        if '/health' in url or '/metrics' in url:
            return None

    return event
