"""Application entry point."""

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
