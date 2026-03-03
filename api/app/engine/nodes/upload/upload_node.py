"""
Upload Node Executor

Handles file upload operations in workflows.
Files are stored in MongoDB GridFS with metadata validation.
File data is also stored in context for downstream nodes to use.
"""

import base64
from collections.abc import Mapping
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.database import get_session
from app.engine.execution_context import ExecutionContext
from app.engine.nodes.base import (
    BaseNode,
    ErrorStrategy,
    NodeExecutionError,
    RetryConfig,
    register_node_executor,
)
from app.engine.nodes.base.emum import NodeExecutionTypeEnum, NodeTypeEnum
from app.engine.nodes.base.entities import ExecuteData
from app.engine.nodes.upload.entities import UploadNodeData
from app.models.workflow.workflow import NodeModel
from app.services.file_server import FileService


@register_node_executor(NodeTypeEnum.UPLOAD)
class UploadNodeExecutor(BaseNode):
    """Executor for upload nodes that handle file uploads."""

    _node_data: UploadNodeData
    execution_type = NodeExecutionTypeEnum.EXECUTABLE

    def __init__(self):
        """Initialize the upload node executor."""
        super().__init__()

    @classmethod
    def version(cls) -> str:
        return '1'

    def init_node_data(self, data: Mapping[str, Any]) -> None:
        self._node_data = UploadNodeData.model_validate(data)

    def _get_error_strategy(self) -> Optional[ErrorStrategy]:
        return self._node_data.error_strategy

    def _get_retry_config(self) -> RetryConfig:
        return self._node_data.retry_config

    def _get_title(self) -> str:
        return self._node_data.title or 'Upload'

    def _get_description(self) -> Optional[str]:
        return self._node_data.desc

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the node configuration.

        Args:
            config: Node configuration dictionary

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            UploadNodeData.model_validate(config)
            return True
        except Exception:
            return False

    async def _get_file_by_id(self, file_id: str) -> tuple[bytes, str, str]:
        """Retrieve file data by ID from FileService.

        Args:
            file_id: String ID of the file to retrieve

        Returns:
            tuple: (file_bytes, filename, content_type)

        Raises:
            NodeExecutionError: If file retrieval fails
        """
        try:
            # Create a database session and FileService instance
            async for session in get_session():
                file_service = FileService(session)
                # Call FileService.download_file to get file reference and stream
                file_reference, file_stream = await file_service.download_file(UUID(file_id))

                # Read all bytes from the async generator
                file_bytes = b''
                async for chunk in file_stream:
                    file_bytes += chunk

                filename = file_reference.filename
                content_type = file_reference.content_type

                return file_bytes, filename, content_type

            # This should not be reached, but added for type safety
            raise NodeExecutionError(
                'Failed to get database session',
                '',
                {'file_id': file_id},
            )
        except NodeExecutionError:
            raise
        except Exception as e:
            raise NodeExecutionError(
                f'Failed to retrieve file: {str(e)}',
                '',
                {'file_id': file_id},
            ) from e

    async def execute(self, node: NodeModel, context: ExecutionContext) -> ExecuteData:
        """Execute upload node by processing file upload.

        Args:
            node: The upload node to execute
            context: The execution context

        Returns:
            ExecuteData containing upload result

        Raises:
            NodeExecutionError: If upload fails
        """
        self.init_node_data(node.config)

        try:
            # Get file data from node config (uploaded via frontend)
            file_id = self._node_data.file_id

            # Parse file data
            try:
                if not file_id or file_id is None:
                    raise NodeExecutionError(
                        'No file uploaded. Please upload a file using the upload button.',
                        str(node.id),
                        {'config': node.config},
                    )
                else:
                    file_bytes, filename, content_type = await self._get_file_by_id(file_id)
            except Exception as e:
                raise NodeExecutionError(
                    f'Failed to parse file data: {str(e)}',
                    str(node.id),
                    {'config': node.config},
                ) from e

            if not file_bytes:
                raise NodeExecutionError(
                    'File data is empty',
                    str(node.id),
                    {'config': node.config},
                )

            # Validate file size
            file_size_mb = len(file_bytes) / (1024 * 1024)
            if file_size_mb > self._node_data.max_size_mb:
                raise NodeExecutionError(
                    f'File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({self._node_data.max_size_mb} MB)',
                    str(node.id),
                    {'file_size_mb': file_size_mb, 'max_size_mb': self._node_data.max_size_mb},
                )

            # Validate file type
            file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
            if file_extension not in self._node_data.allowed_types:
                raise NodeExecutionError(
                    f'File type .{file_extension} is not allowed. Allowed types: {self._node_data.allowed_types}',
                    str(node.id),
                    {
                        'file_extension': file_extension,
                        'allowed_types': self._node_data.allowed_types,
                    },
                )

            # Get tenant and user info from workflow
            tenant_id = context.workflow.workspace_id
            user_id = context.workflow.created_by

            # Upload file to MongoDB (file is already uploaded, just return the file_id)
            # Note: The file was already uploaded via the frontend and stored in GridFS
            # We just need to return the existing file_id and metadata
            upload_result = {
                'id': file_id,
                'name': filename,
                'size': len(file_bytes),
                'extension': file_extension,
                'mime_type': content_type,
                'hash': '',  # Hash is already stored in GridFS
                'created_at': None,
            }

            # Prepare output data
            output_data = {
                'file_id': upload_result['id'],
                'filename': upload_result['name'],
                'size': upload_result['size'],
                'size_mb': round(upload_result['size'] / (1024 * 1024), 2),
                'extension': upload_result['extension'],
                'mime_type': upload_result['mime_type'],
                'hash': upload_result['hash'],
                'created_at': upload_result['created_at'].isoformat()
                if upload_result.get('created_at')
                else None,
                'success': True,
                # Store file stream/bytes for downstream nodes
                'file_stream': file_bytes,
                'file_base64': base64.b64encode(file_bytes).decode('utf-8'),
            }

            return ExecuteData(title=self._get_title(), output=output_data)

        except NodeExecutionError:
            raise
        except Exception as e:
            raise NodeExecutionError(
                f'File upload failed: {str(e)}',
                str(node.id),
                {'config': node.config},
            ) from e

    def get_required_inputs(self) -> List[str]:
        """Get the list of required input parameters.

        Returns:
            List of required input parameter names
        """
        return []  # No external inputs required, file comes from node config

    def get_output_schema(self) -> Dict[str, Any]:
        """Get the output schema for upload nodes.

        Returns:
            Dictionary describing the output schema
        """
        return {
            'file_id': {'type': 'string', 'description': 'Unique file identifier in MongoDB'},
            'filename': {'type': 'string', 'description': 'Original filename'},
            'size': {'type': 'integer', 'description': 'File size in bytes'},
            'size_mb': {'type': 'number', 'description': 'File size in MB'},
            'extension': {'type': 'string', 'description': 'File extension'},
            'mime_type': {'type': 'string', 'description': 'MIME type of the file'},
            'hash': {'type': 'string', 'description': 'SHA256 hash of the file'},
            'created_at': {'type': 'string', 'description': 'Upload timestamp (ISO format)'},
            'success': {'type': 'boolean', 'description': 'Whether upload was successful'},
            'file_stream': {
                'type': 'bytes',
                'description': 'Raw file bytes for downstream processing',
            },
            'file_base64': {'type': 'string', 'description': 'Base64 encoded file data'},
        }
