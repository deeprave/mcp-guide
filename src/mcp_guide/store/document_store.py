"""SQLite-backed document store."""

import json
import sqlite3
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Optional

from mcp_guide.config_paths import get_documents_db
from mcp_guide.store.executor import run_in_thread

SourceType = Literal["file", "url"]

_VALID_SOURCE_TYPES: frozenset[str] = frozenset({"file", "url"})

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL COLLATE NOCASE,
    name        TEXT NOT NULL COLLATE NOCASE,
    source      TEXT NOT NULL,
    source_type TEXT NOT NULL,
    content     TEXT NOT NULL,
    metadata    BLOB DEFAULT NULL,
    mtime       REAL DEFAULT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE (category, name)
);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents (category);
CREATE INDEX IF NOT EXISTS idx_documents_name ON documents (name);
"""

# Additive-only migrations — use ALTER TABLE ... ADD COLUMN IF NOT EXISTS.
# Never drop, rename, or change column types (requires table rebuild).
_MIGRATIONS = """
"""


@dataclass
class DocumentRecord:
    id: int
    category: str
    name: str
    source: str
    source_type: str
    metadata: dict
    created_at: str
    updated_at: str
    content: Optional[str] = None
    mtime: Optional[float] = None


def _get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open connection and ensure schema exists."""
    path = db_path or get_documents_db()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_CREATE_TABLE)
    if _MIGRATIONS.strip():
        for statement in _MIGRATIONS.strip().split(";"):
            statement = statement.strip()
            if statement:
                try:
                    conn.execute(statement)
                except sqlite3.OperationalError:
                    pass  # Column already exists — migration already applied
    return conn


def _now() -> str:
    return datetime.now(UTC).isoformat()


# Derive metadata-only query from DocumentRecord fields, excluding content.
_METADATA_FIELDS = tuple(f.name for f in fields(DocumentRecord) if f.name != "content")
_SELECT_METADATA = "SELECT " + ", ".join(_METADATA_FIELDS) + " FROM documents"  # nosec B608


def _parse_metadata(raw: str | None) -> dict:
    result = json.loads(raw) if raw else {}
    return result if isinstance(result, dict) else {}


def _row_to_record(row: sqlite3.Row) -> DocumentRecord:
    """Convert a full row (with content) to DocumentRecord."""
    return DocumentRecord(
        id=row["id"],
        category=row["category"],
        name=row["name"],
        source=row["source"],
        source_type=row["source_type"],
        metadata=_parse_metadata(row["metadata"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        content=row["content"],
        mtime=row["mtime"],
    )


def _row_to_metadata_record(row: sqlite3.Row) -> DocumentRecord:
    """Convert a content-less row to DocumentRecord (content remains None)."""
    return DocumentRecord(
        id=row["id"],
        category=row["category"],
        name=row["name"],
        source=row["source"],
        source_type=row["source_type"],
        metadata=_parse_metadata(row["metadata"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        mtime=row["mtime"],
    )


def _add_document(
    category: str,
    name: str,
    source: str,
    source_type: str,
    content: str,
    metadata: Optional[dict] = None,
    mtime: Optional[float] = None,
    db_path: Optional[Path] = None,
) -> DocumentRecord:
    if not category or not name:
        raise ValueError("category and name must be non-empty")
    if source_type not in _VALID_SOURCE_TYPES:
        raise ValueError(f"source_type must be one of {sorted(_VALID_SOURCE_TYPES)}, got {source_type!r}")
    now = _now()
    meta_json = json.dumps(metadata) if metadata else None
    conn = _get_conn(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO documents (category, name, source, source_type, content, metadata, mtime, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (category, name) DO UPDATE SET
                    source      = excluded.source,
                    source_type = excluded.source_type,
                    content     = excluded.content,
                    metadata    = excluded.metadata,
                    mtime       = excluded.mtime,
                    updated_at  = excluded.updated_at
                """,
                (category, name, source, source_type, content, meta_json, mtime, now, now),
            )
            row = conn.execute(
                "SELECT * FROM documents WHERE category = ? AND name = ?",
                (category, name),
            ).fetchone()
    finally:
        conn.close()
    return _row_to_record(row)


def _get_document(category: str, name: str, db_path: Optional[Path] = None) -> Optional[DocumentRecord]:
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            _SELECT_METADATA + " WHERE category = ? AND name = ?",
            (category, name),
        ).fetchone()
    finally:
        conn.close()
    return _row_to_metadata_record(row) if row else None


def _get_document_content(category: str, name: str, db_path: Optional[Path] = None) -> Optional[str]:
    conn = _get_conn(db_path)
    try:
        row = conn.execute(
            "SELECT content FROM documents WHERE category = ? AND name = ?",
            (category, name),
        ).fetchone()
    finally:
        conn.close()
    return row["content"] if row else None


def _remove_document(category: str, name: str, db_path: Optional[Path] = None) -> bool:
    conn = _get_conn(db_path)
    try:
        with conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE category = ? AND name = ?",
                (category, name),
            )
        rowcount = cursor.rowcount
    finally:
        conn.close()
    return rowcount > 0


def _list_documents(category: Optional[str] = None, db_path: Optional[Path] = None) -> list[DocumentRecord]:
    conn = _get_conn(db_path)
    try:
        if category is not None:
            rows = conn.execute(
                _SELECT_METADATA + " WHERE category = ? ORDER BY name",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(_SELECT_METADATA + " ORDER BY category, name").fetchall()
    finally:
        conn.close()
    return [_row_to_metadata_record(r) for r in rows]


def _update_document(
    category: str,
    name: str,
    *,
    new_name: Optional[str] = None,
    new_category: Optional[str] = None,
    metadata_add: Optional[dict] = None,
    metadata_replace: Optional[dict] = None,
    metadata_clear: Optional[list[str]] = None,
    db_path: Optional[Path] = None,
) -> Optional[DocumentRecord]:
    # Validate at least one mutation
    has_rename = new_name is not None or new_category is not None
    meta_ops = sum(x is not None for x in (metadata_add, metadata_replace, metadata_clear))
    if not has_rename and meta_ops == 0:
        raise ValueError("At least one mutation parameter is required")
    if meta_ops > 1:
        raise ValueError("metadata_add, metadata_replace, and metadata_clear are mutually exclusive")

    conn = _get_conn(db_path)
    try:
        with conn:
            row = conn.execute(
                _SELECT_METADATA + " WHERE category = ? AND name = ?",
                (category, name),
            ).fetchone()
            if not row:
                return None

            target_cat = new_category if new_category is not None else category
            target_name = new_name if new_name is not None else name

            # Check collision if renaming/moving, excluding the current row (handles case-only renames)
            if target_cat != category or target_name != name:
                existing = conn.execute(
                    "SELECT 1 FROM documents WHERE category = ? AND name = ? AND NOT (category = ? AND name = ?)",
                    (target_cat, target_name, category, name),
                ).fetchone()
                if existing:
                    raise ValueError(f"Document {target_cat}/{target_name} already exists")

            # Apply metadata mutation
            metadata = _parse_metadata(row["metadata"])
            if metadata_clear is not None:
                for key in metadata_clear:
                    metadata.pop(key, None)
            elif metadata_replace is not None:
                metadata = metadata_replace
            elif metadata_add is not None:
                metadata.update(metadata_add)

            now = _now()
            meta_json = json.dumps(metadata) if metadata is not None else None
            conn.execute(
                "UPDATE documents SET category = ?, name = ?, metadata = ?, updated_at = ? WHERE category = ? AND name = ?",
                (target_cat, target_name, meta_json, now, category, name),
            )
            updated = conn.execute(
                _SELECT_METADATA + " WHERE category = ? AND name = ?",
                (target_cat, target_name),
            ).fetchone()
    finally:
        conn.close()
    return _row_to_metadata_record(updated) if updated else None


# --- Async public API ---


async def add_document(
    category: str,
    name: str,
    source: str,
    source_type: SourceType,
    content: str,
    metadata: Optional[dict] = None,
    mtime: Optional[float] = None,
    db_path: Optional[Path] = None,
) -> DocumentRecord:
    """Insert or update a document. Returns the stored record."""
    return await run_in_thread(_add_document, category, name, source, source_type, content, metadata, mtime, db_path)


async def get_document(category: str, name: str, db_path: Optional[Path] = None) -> Optional[DocumentRecord]:
    """Return document by (category, name) without content, or None if not found."""
    return await run_in_thread(_get_document, category, name, db_path)


async def get_document_content(category: str, name: str, db_path: Optional[Path] = None) -> Optional[str]:
    """Return document content by (category, name), or None if not found."""
    return await run_in_thread(_get_document_content, category, name, db_path)


async def remove_document(category: str, name: str, db_path: Optional[Path] = None) -> bool:
    """Delete document by (category, name). Returns True if a row was deleted."""
    return await run_in_thread(_remove_document, category, name, db_path)


async def list_documents(category: Optional[str] = None, db_path: Optional[Path] = None) -> list[DocumentRecord]:
    """List documents, optionally filtered by category."""
    return await run_in_thread(_list_documents, category, db_path)


async def update_document(
    category: str,
    name: str,
    *,
    new_name: Optional[str] = None,
    new_category: Optional[str] = None,
    metadata_add: Optional[dict] = None,
    metadata_replace: Optional[dict] = None,
    metadata_clear: Optional[list[str]] = None,
    db_path: Optional[Path] = None,
) -> Optional[DocumentRecord]:
    """Update a document in-place. Returns updated record, or None if not found."""
    return await run_in_thread(
        _update_document,
        category,
        name,
        new_name=new_name,
        new_category=new_category,
        metadata_add=metadata_add,
        metadata_replace=metadata_replace,
        metadata_clear=metadata_clear,
        db_path=db_path,
    )
