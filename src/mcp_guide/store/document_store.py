"""SQLite-backed document store."""

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from mcp_guide.config_paths import get_documents_db

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,
    name        TEXT NOT NULL,
    source      TEXT NOT NULL,
    source_type TEXT NOT NULL,
    content     TEXT NOT NULL,
    metadata    BLOB DEFAULT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE (category, name)
);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents (category);
CREATE INDEX IF NOT EXISTS idx_documents_name ON documents (name);
"""


@dataclass
class DocumentRecord:
    id: int
    category: str
    name: str
    source: str
    source_type: str
    content: str
    metadata: dict
    created_at: str
    updated_at: str


_initialized: set[Path] = set()


def _get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open connection and ensure schema exists (schema created once per db path)."""
    path = db_path or get_documents_db()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    if path not in _initialized:
        conn.executescript(_CREATE_TABLE)
        _initialized.add(path)
    return conn


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _row_to_record(row: sqlite3.Row) -> DocumentRecord:
    return DocumentRecord(
        id=row["id"],
        category=row["category"],
        name=row["name"],
        source=row["source"],
        source_type=row["source_type"],
        content=row["content"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def add_document(
    category: str,
    name: str,
    source: str,
    source_type: str,
    content: str,
    metadata: Optional[dict] = None,
    db_path: Optional[Path] = None,
) -> DocumentRecord:
    """Insert or update a document. Returns the stored record."""
    now = _now()
    meta_json = json.dumps(metadata) if metadata else None
    conn = _get_conn(db_path)
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO documents (category, name, source, source_type, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (category, name) DO UPDATE SET
                    source      = excluded.source,
                    source_type = excluded.source_type,
                    content     = excluded.content,
                    metadata    = excluded.metadata,
                    updated_at  = excluded.updated_at
                """,
                (category, name, source, source_type, content, meta_json, now, now),
            )
            row = conn.execute("SELECT * FROM documents WHERE category = ? AND name = ?", (category, name)).fetchone()
    finally:
        conn.close()
    return _row_to_record(row)


def get_document(category: str, name: str, db_path: Optional[Path] = None) -> Optional[DocumentRecord]:
    """Return document by (category, name), or None if not found."""
    conn = _get_conn(db_path)
    try:
        row = conn.execute("SELECT * FROM documents WHERE category = ? AND name = ?", (category, name)).fetchone()
    finally:
        conn.close()
    return _row_to_record(row) if row else None


def remove_document(category: str, name: str, db_path: Optional[Path] = None) -> bool:
    """Delete document by (category, name). Returns True if a row was deleted."""
    conn = _get_conn(db_path)
    try:
        with conn:
            cursor = conn.execute("DELETE FROM documents WHERE category = ? AND name = ?", (category, name))
        rowcount = cursor.rowcount
    finally:
        conn.close()
    return rowcount > 0


def list_documents(category: Optional[str] = None, db_path: Optional[Path] = None) -> list[DocumentRecord]:
    """List documents, optionally filtered by category."""
    conn = _get_conn(db_path)
    try:
        if category is not None:
            rows = conn.execute("SELECT * FROM documents WHERE category = ? ORDER BY name", (category,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY category, name").fetchall()
    finally:
        conn.close()
    return [_row_to_record(r) for r in rows]
