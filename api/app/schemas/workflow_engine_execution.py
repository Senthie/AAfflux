"""
Author: Senthie seemoon2077@gmail.com
Date: 2026-02-07 16:58:39
LastEditors: Senthie seemoon2077@gmail.com
LastEditTime: 2026-02-07 17:01:06
FilePath: /api/app/schemas/workflow_engine_execution.py
Description: 用于 workflow engine and execution schemas

Copyright (c) 2026 by Senthie email: seemoon2077@gmail.com, All Rights Reserved.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.workflow.workflow import GraphModel


class WorkflowEngineModel(BaseModel):
    """
    used for workflow engine processing
    用在 workflow 的引擎中传递
    """

    id: UUID
    name: str
    description: Optional[str]
    workspace_id: UUID
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    is_deleted: bool = False
    graph: GraphModel
    model_config = {'from_attributes': True}
