"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-02 08:50:10
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-09 10:59:51
FilePath: /api/main.py
Description: Application entry point.
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
