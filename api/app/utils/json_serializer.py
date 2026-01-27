"""
Author: kk123047 3254834740@qq.com
Date: 2025-12-09 18:00:00
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-01-27 17:57:12
FilePath: /api/app/utils/json_serializer.py
Description: Json Serializer工具

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import date, datetime
from decimal import Decimal
import json
from typing import Any
from uuid import UUID


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID, datetime, and other types."""

    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation of the object
        """
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            # Handle custom objects by converting to dict
            return obj.__dict__

        return super().default(obj)


def json_dumps(obj: Any, **kwargs) -> str:
    """JSON dumps with custom encoder.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string representation
    """
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


def json_dumps_sorted(obj: Any, **kwargs) -> str:
    """JSON dumps with custom encoder and sorted keys for consistent hashing.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string representation with sorted keys
    """
    return json.dumps(obj, cls=CustomJSONEncoder, sort_keys=True, **kwargs)


def serialize_for_db(obj: Any) -> Any:
    """Serialize object for database storage, converting UUIDs and other types to JSON-safe formats.

    This is particularly useful for Pydantic models that contain UUID fields
    that need to be stored in JSONB database columns.

    Args:
        obj: Object to serialize (typically a Pydantic model)

    Returns:
        JSON-safe dictionary representation
    """
    return json.loads(json.dumps(obj, cls=CustomJSONEncoder))
