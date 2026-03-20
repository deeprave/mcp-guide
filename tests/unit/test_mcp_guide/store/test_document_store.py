"""Tests for document_store CRUD operations."""

import pytest

from mcp_guide.store.document_store import (
    add_document,
    get_document,
    list_documents,
    remove_document,
)


@pytest.fixture
def db(tmp_path):
    return tmp_path / "test_documents.db"


def test_add_and_get_round_trip(db):
    record = add_document("docs", "readme", "/path/readme.md", "file", "# Hello", db_path=db)
    assert record.category == "docs"
    assert record.name == "readme"
    assert record.content == "# Hello"
    assert record.source_type == "file"

    fetched = get_document("docs", "readme", db_path=db)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.content == "# Hello"


def test_upsert_updates_content_and_timestamp(db):
    first = add_document("docs", "readme", "/path/readme.md", "file", "v1", db_path=db)
    second = add_document("docs", "readme", "/path/readme.md", "file", "v2", db_path=db)
    assert second.content == "v2"
    assert second.id == first.id
    assert second.updated_at >= first.updated_at


def test_get_missing_returns_none(db):
    assert get_document("docs", "nonexistent", db_path=db) is None


def test_remove_existing_returns_true(db):
    add_document("docs", "readme", "/path/readme.md", "file", "# Hello", db_path=db)
    assert remove_document("docs", "readme", db_path=db) is True
    assert get_document("docs", "readme", db_path=db) is None


def test_remove_missing_returns_false(db):
    assert remove_document("docs", "nonexistent", db_path=db) is False


def test_list_by_category(db):
    add_document("docs", "a", "/a", "file", "A", db_path=db)
    add_document("docs", "b", "/b", "file", "B", db_path=db)
    add_document("other", "c", "/c", "file", "C", db_path=db)

    results = list_documents("docs", db_path=db)
    assert len(results) == 2
    assert {r.name for r in results} == {"a", "b"}


def test_list_all(db):
    add_document("docs", "a", "/a", "file", "A", db_path=db)
    add_document("other", "b", "/b", "url", "B", db_path=db)

    results = list_documents(db_path=db)
    assert len(results) == 2


def test_metadata_stored_and_retrieved(db):
    meta = {"etag": "abc123", "content-type": "text/markdown"}
    record = add_document("docs", "readme", "/path", "url", "content", metadata=meta, db_path=db)
    assert record.metadata == meta

    fetched = get_document("docs", "readme", db_path=db)
    assert fetched is not None
    assert fetched.metadata == meta
