"""文件域模型"""

from api.app.models.file.reference import FileReference

__all__ = [
    "FileReference",
]


def get_file_service():
    """Lazy import file service to avoid config dependency."""
    from api.app.models.file.service import file_service
    return file_service
