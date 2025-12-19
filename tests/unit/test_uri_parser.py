"""Unit tests for URI parsing utility."""

import pytest

from mcp_guide.uri_parser import GuideUri, parse_guide_uri


class TestGuideUriParsing:
    """Test guide:// URI parsing functionality."""

    def test_parse_collection_only(self) -> None:
        """Test parsing URI with collection only."""
        result = parse_guide_uri("guide://lang")

        assert result.collection == "lang"
        assert result.document is None

    def test_parse_collection_with_document(self) -> None:
        """Test parsing URI with collection and document."""
        result = parse_guide_uri("guide://lang/python")

        assert result.collection == "lang"
        assert result.document == "python"

    def test_parse_collection_with_complex_document(self) -> None:
        """Test parsing URI with complex document pattern."""
        result = parse_guide_uri("guide://docs/api/v1/auth")

        assert result.collection == "docs"
        assert result.document == "api/v1/auth"

    def test_parse_invalid_scheme(self) -> None:
        """Test parsing URI with invalid scheme raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URI scheme: expected 'guide', got 'http'"):
            parse_guide_uri("http://lang/python")

    def test_parse_missing_collection(self) -> None:
        """Test parsing URI without collection raises ValueError."""
        with pytest.raises(ValueError, match="URI must specify a collection"):
            parse_guide_uri("guide://")

    def test_parse_empty_path(self) -> None:
        """Test parsing URI with empty path (just slash)."""
        result = parse_guide_uri("guide://lang/")

        assert result.collection == "lang"
        assert result.document is None

    def test_parse_collection_with_hyphen(self) -> None:
        """Test parsing collection name with hyphen."""
        result = parse_guide_uri("guide://api-docs/reference")

        assert result.collection == "api-docs"
        assert result.document == "reference"

    def test_parse_collection_with_underscore(self) -> None:
        """Test parsing collection name with underscore."""
        result = parse_guide_uri("guide://user_guides/intro")

        assert result.collection == "user_guides"
        assert result.document == "intro"

    def test_guide_uri_dataclass(self) -> None:
        """Test GuideUri dataclass creation."""
        uri = GuideUri(collection="test")
        assert uri.collection == "test"
        assert uri.document is None

        uri_with_doc = GuideUri(collection="test", document="doc")
        assert uri_with_doc.collection == "test"
        assert uri_with_doc.document == "doc"
