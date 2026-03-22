"""Tests for document_store CRUD operations."""

import sqlite3

import pytest

from mcp_guide.store.document_store import (
    _get_conn,
    add_document,
    get_document,
    get_document_content,
    list_documents,
    remove_document,
)


@pytest.fixture
def db(tmp_path):
    return tmp_path / "test_documents.db"


@pytest.mark.anyio
async def test_add_and_get_round_trip(db):
    record = await add_document("docs", "readme", "/path/readme.md", "file", "# Hello", db_path=db)
    assert record.category == "docs"
    assert record.name == "readme"
    assert record.content == "# Hello"
    assert record.source_type == "file"

    fetched = await get_document("docs", "readme", db_path=db)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.content is None  # get_document excludes content


@pytest.mark.anyio
async def test_get_document_content_returns_content(db):
    await add_document("docs", "readme", "/path/readme.md", "file", "# Hello", db_path=db)
    content = await get_document_content("docs", "readme", db_path=db)
    assert content == "# Hello"


@pytest.mark.anyio
async def test_get_document_content_missing_returns_none(db):
    assert await get_document_content("docs", "nonexistent", db_path=db) is None


@pytest.mark.anyio
async def test_upsert_updates_content_and_timestamp(db):
    first = await add_document("docs", "readme", "/path/readme.md", "file", "v1", db_path=db)
    second = await add_document("docs", "readme", "/path/readme.md", "file", "v2", db_path=db)
    assert second.content == "v2"
    assert second.id == first.id
    assert second.updated_at >= first.updated_at

    content = await get_document_content("docs", "readme", db_path=db)
    assert content == "v2"


@pytest.mark.anyio
async def test_get_missing_returns_none(db):
    assert await get_document("docs", "nonexistent", db_path=db) is None


@pytest.mark.anyio
async def test_remove_existing_returns_true(db):
    await add_document("docs", "readme", "/path/readme.md", "file", "# Hello", db_path=db)
    assert await remove_document("docs", "readme", db_path=db) is True
    assert await get_document("docs", "readme", db_path=db) is None


@pytest.mark.anyio
async def test_remove_missing_returns_false(db):
    assert await remove_document("docs", "nonexistent", db_path=db) is False


@pytest.mark.anyio
async def test_list_by_category(db):
    await add_document("docs", "a", "/a", "file", "A", db_path=db)
    await add_document("docs", "b", "/b", "file", "B", db_path=db)
    await add_document("other", "c", "/c", "file", "C", db_path=db)

    results = await list_documents("docs", db_path=db)
    assert len(results) == 2
    assert {r.name for r in results} == {"a", "b"}
    assert all(r.content is None for r in results)  # list excludes content


@pytest.mark.anyio
async def test_list_all(db):
    await add_document("docs", "a", "/a", "file", "A", db_path=db)
    await add_document("other", "b", "/b", "url", "B", db_path=db)

    results = await list_documents(db_path=db)
    assert len(results) == 2
    assert all(r.content is None for r in results)


@pytest.mark.anyio
async def test_metadata_stored_and_retrieved(db):
    meta = {"etag": "abc123", "content-type": "text/markdown"}
    record = await add_document("docs", "readme", "/path", "url", "content", metadata=meta, db_path=db)
    assert record.metadata == meta

    fetched = await get_document("docs", "readme", db_path=db)
    assert fetched is not None
    assert fetched.metadata == meta


@pytest.mark.anyio
async def test_invalid_source_type_raises(db):
    with pytest.raises(ValueError, match="source_type"):
        await add_document("docs", "readme", "/path", "ftp", "content", db_path=db)  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_empty_category_raises(db):
    with pytest.raises(ValueError, match="category"):
        await add_document("", "readme", "/path", "file", "content", db_path=db)


@pytest.mark.anyio
async def test_empty_name_raises(db):
    with pytest.raises(ValueError, match="name"):
        await add_document("docs", "", "/path", "file", "content", db_path=db)


@pytest.mark.anyio
async def test_mtime_stored_on_add(db):
    """mtime is persisted and returned on add."""
    record = await add_document("docs", "readme", "/path", "file", "content", mtime=1700000000.5, db_path=db)
    assert record.mtime == 1700000000.5


@pytest.mark.anyio
async def test_mtime_returned_on_get(db):
    """mtime is included in metadata-only get."""
    await add_document("docs", "readme", "/path", "file", "content", mtime=1700000000.0, db_path=db)
    fetched = await get_document("docs", "readme", db_path=db)
    assert fetched is not None
    assert fetched.mtime == 1700000000.0


@pytest.mark.anyio
async def test_mtime_returned_on_list(db):
    """mtime is included in list results."""
    await add_document("docs", "a", "/path", "file", "content", mtime=100.0, db_path=db)
    await add_document("docs", "b", "/path", "file", "content", db_path=db)
    results = await list_documents("docs", db_path=db)
    assert results[0].mtime == 100.0
    assert results[1].mtime is None


@pytest.mark.anyio
async def test_mtime_defaults_to_none(db):
    """mtime defaults to None when not provided."""
    record = await add_document("docs", "readme", "/path", "file", "content", db_path=db)
    assert record.mtime is None


@pytest.mark.anyio
async def test_mtime_updated_on_upsert(db):
    """mtime is updated when document is upserted."""
    await add_document("docs", "readme", "/path", "file", "v1", mtime=100.0, db_path=db)
    record = await add_document("docs", "readme", "/path", "file", "v2", mtime=200.0, db_path=db)
    assert record.mtime == 200.0


@pytest.mark.anyio
async def test_migration_adds_mtime_to_existing_db(tmp_path):
    """Opening a pre-existing DB without mtime column runs the migration."""
    db = tmp_path / "legacy.db"
    # Create a legacy schema without the mtime column
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL COLLATE NOCASE,
            name        TEXT NOT NULL COLLATE NOCASE,
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
    """)
    conn.execute(
        "INSERT INTO documents (category, name, source, source_type, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("docs", "old.md", "/path", "file", "# Old", "2020-01-01T00:00:00+00:00", "2020-01-01T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    # Opening the DB via _get_conn should run the migration
    conn2 = _get_conn(db)
    conn2.close()

    # Verify the mtime column now exists and returns NULL for the old row
    record = await get_document("docs", "old.md", db_path=db)
    assert record is not None
    assert record.mtime is None


@pytest.mark.anyio
async def test_migration_is_idempotent(tmp_path):
    """Running migration on a DB that already has the mtime column is a no-op."""
    db = tmp_path / "new.db"
    # First open creates the schema with mtime already included
    _get_conn(db).close()
    # Second open should not raise even though mtime already exists
    _get_conn(db).close()
    record = await add_document("docs", "readme.md", "/path", "file", "content", mtime=1.0, db_path=db)
    assert record.mtime == 1.0
