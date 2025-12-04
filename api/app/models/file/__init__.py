"""文件域模型"""

from app.models.file.reference import FileReference

__all__ = [
    "FileReference",
]


def get_file_service():
    """Lazy import file service to avoid config dependency."""
    from app.models.file.service import file_service

    return file_service
