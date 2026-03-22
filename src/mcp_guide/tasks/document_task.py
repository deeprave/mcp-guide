"""DocumentTask - ingests documents into the store via FS_FILE_CONTENT events."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from mcp_guide.content.formatters.mime import detect_text_subtype
from mcp_guide.core.mcp_log import get_logger
from mcp_guide.decorators import task_init
from mcp_guide.session import get_session
from mcp_guide.store.document_store import add_document, get_document
from mcp_guide.task_manager.interception import EventType
from mcp_guide.task_manager.manager import get_task_manager

if TYPE_CHECKING:
    from mcp_guide.task_manager.manager import EventResult, TaskManager

logger = get_logger(__name__)

# Required metadata fields that distinguish a document ingestion event
_REQUIRED_FIELDS = frozenset({"category", "source"})

_DEFAULT_DOC_TYPE = "agent/instruction"
_VALID_DOC_TYPES = frozenset({"agent/instruction", "agent/information", "user/information"})


@task_init
class DocumentTask:
    """Ingest documents into the store when FS_FILE_CONTENT events contain required metadata."""

    def __init__(self, task_manager: Optional["TaskManager"] = None) -> None:
        if task_manager is None:
            task_manager = get_task_manager()
        self.task_manager = task_manager
        self.task_manager.subscribe(self, EventType.FS_FILE_CONTENT)

    def get_name(self) -> str:
        return "DocumentTask"

    async def on_init(self) -> None:
        pass

    async def on_tool(self) -> None:
        pass

    async def handle_event(self, event_type: EventType, data: dict[str, Any]) -> "EventResult | None":
        """Handle FS_FILE_CONTENT events for document ingestion."""
        from mcp_guide.task_manager.manager import EventResult

        if not (event_type & EventType.FS_FILE_CONTENT):
            return None

        # Only match events with required metadata fields
        if not _REQUIRED_FIELDS.issubset(data):
            return None

        category = data["category"]
        source = data["source"]
        content = data.get("content", "")
        mtime = data.get("mtime")
        force = data.get("force", False)
        doc_type = data.get("type", _DEFAULT_DOC_TYPE)
        name = data.get("name") or Path(data.get("path", "")).name

        # Type validation/coercion to guard against agent-provided non-string values
        if not isinstance(category, str):
            return EventResult(result=False, message=f"Invalid category type: expected str, got {type(category).__name__}")
        if not isinstance(source, str):
            return EventResult(result=False, message=f"Invalid source type: expected str, got {type(source).__name__}")
        if not isinstance(content, str):
            try:
                content = str(content)
            except Exception:
                return EventResult(result=False, message="content could not be coerced to string")
        if mtime is not None:
            # bool is a subclass of int in Python, so the bool guard must come first
            if isinstance(mtime, bool) or not isinstance(mtime, (int, float)):
                return EventResult(result=False, message=f"Invalid mtime type: expected number, got {type(mtime).__name__}")
            mtime = float(mtime)

        if not name:
            return EventResult(result=False, message="Document name could not be determined")

        if doc_type not in _VALID_DOC_TYPES:
            return EventResult(result=False, message=f"Invalid document type: {doc_type!r}")

        # Validate category exists
        session = await get_session()
        project = await session.get_project()
        if category not in project.categories:
            return EventResult(result=False, message=f"Category {category!r} does not exist")

        # Check mtime staleness against existing document
        if mtime is not None and not force:
            existing = await get_document(category, name)
            if existing is not None and existing.mtime is not None:
                if mtime == existing.mtime:
                    return EventResult(result=False, message=f"Document {category}/{name} unchanged (same mtime)")
                if mtime < existing.mtime:
                    return EventResult(result=False, message=f"Document {category}/{name} is newer than source")

        # Auto-detect content-type
        content_type = detect_text_subtype(content)

        metadata = {"content-type": content_type, "type": doc_type}

        # Determine source_type from source string
        source_type = "url" if source.startswith(("http://", "https://")) else "file"

        record = await add_document(
            category=category,
            name=name,
            source=source,
            source_type=source_type,
            content=content,
            metadata=metadata,
            mtime=mtime,
        )

        logger.info(f"Ingested document {record.category}/{record.name} (source={source_type})")
        return EventResult(result=True, message=f"Document {category}/{name} stored successfully")
