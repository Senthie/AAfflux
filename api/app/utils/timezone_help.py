"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-01-05 16:38:49
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-05 18:01:13
FilePath: /api/app/utils/timezone_help.py
Description: 时区工具模块 用来规范获取时间和输出时间

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
import os
import time
from typing import Optional

try:
    from zoneinfo import ZoneInfo

    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False
    try:
        import pytz

        PYTZ_AVAILABLE = True
    except ImportError:
        PYTZ_AVAILABLE = False


class TimezoneHelper:
    """时区助手类"""

    def __init__(self, default_tz: Optional[str] = None):
        """
        初始化时区助手

        Args:
            default_tz: 默认时区，如 'Asia/Shanghai', 'UTC', 'America/New_York'
                        如果为None，则使用系统时区
        """
        self.default_tz = default_tz or self.get_system_timezone()

    def get_current_time(self, timezone: Optional[str] = None) -> datetime:
        """
        获取指定时区的当前时间

        Args:
            timezone: 时区名称，如果为None则使用默认时区

        Returns:
            带时区信息的datetime对象
        """
        tz = timezone or self.default_tz

        if ZONEINFO_AVAILABLE:
            return datetime.now(ZoneInfo(tz))
        elif PYTZ_AVAILABLE:
            return datetime.now(pytz.timezone(tz))
        else:
            raise ImportError('需要安装 zoneinfo (Python 3.9+) 或 pytz 库')

    def format_time(self, dt: datetime, fmt: str | None = None) -> str:
        """
        格式化时间，包含时区信息

        Args:
            dt: datetime对象
            fmt: 格式化字符串，默认包含时区

        Returns:
            格式化后的时间字符串
        """
        if fmt is None:
            fmt = '%Y-%m-%d %H:%M:%S %Z (UTC%z)'

        return dt.strftime(fmt)

    def get_system_timezone(self) -> str:
        """
        获取系统时区

        Returns:
            时区名称字符串
        """
        if os.name == 'nt':  # Windows
            # Windows系统，使用tzlocal或返回UTC
            try:
                import tzlocal

                return str(tzlocal.get_localzone())
            except ImportError:
                return 'UTC'
        else:  # Linux/macOS
            # 从环境变量获取
            if 'TZ' in os.environ:
                return os.environ['TZ']

            # 从time模块获取
            tz_name = time.tzname[0]
            if time.daylight and time.localtime().tm_isdst > 0:
                tz_name = time.tzname[1]

            # 转换为标准时区名称（简化版，实际需要更复杂的映射）
            tz_mapping = {
                'CST': 'Asia/Shanghai',
                'EST': 'America/New_York',
                'PST': 'America/Los_Angeles',
                'GMT': 'UTC',
                'UTC': 'UTC',
            }

            return tz_mapping.get(tz_name, 'UTC')

    def convert_timezone(self, dt: datetime, to_tz: str) -> datetime:
        """
        转换时区

        Args:
            dt: 原始datetime对象
            to_tz: 目标时区

        Returns:
            转换后的datetime对象
        """
        if dt.tzinfo is None:
            # 如果原始时间没有时区信息，假设为UTC
            if ZONEINFO_AVAILABLE:
                dt = dt.replace(tzinfo=ZoneInfo('UTC'))
            elif PYTZ_AVAILABLE:
                dt = pytz.UTC.localize(dt)

        # 转换时区
        if ZONEINFO_AVAILABLE:
            return dt.astimezone(ZoneInfo(to_tz))
        elif PYTZ_AVAILABLE:
            return dt.astimezone(pytz.timezone(to_tz))
        else:
            raise ImportError('需要安装 zoneinfo (Python 3.9+) 或 pytz 库')

    @staticmethod
    def get_all_timezones() -> list:
        """
        获取所有可用的时区

        Returns:
            时区名称列表
        """
        if ZONEINFO_AVAILABLE:
            import zoneinfo

            return sorted(zoneinfo.available_timezones())
        elif PYTZ_AVAILABLE:
            return pytz.all_timezones
        else:
            return ['UTC']


tz_helper = TimezoneHelper()
# 使用示例
if __name__ == '__main__':
    # 创建时区助手实例

    # 获取当前时间（使用默认时区）
    current_time = tz_helper.get_current_time()
    print(f'当前时间: {tz_helper.format_time(current_time)}')

    # 获取UTC时间
    utc_time = tz_helper.get_current_time('UTC')
    print(f'UTC时间: {tz_helper.format_time(utc_time)}')

    # 获取纽约时间
    ny_time = tz_helper.get_current_time('America/New_York')
    print(f'纽约时间: {tz_helper.format_time(ny_time)}')

    # 时区转换示例
    converted = tz_helper.convert_timezone(utc_time, 'Asia/Shanghai')
    print(f'UTC转换为北京时间: {tz_helper.format_time(converted)}')

    # 自定义格式
    custom_format = '%A, %B %d, %Y %I:%M:%S %p %Z'
    print(f'自定义格式: {tz_helper.format_time(current_time, custom_format)}')
