"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:36:55
FilePath: /api/main.py
Description: 应用入口点

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""
import uvicorn

from app.core.config import settings


def main() -> None:
    """Run the application."""
    uvicorn.run(
        'app.main:app',
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level='debug' if settings.debug else 'info',
    )


if __name__ == '__main__':
    main()
