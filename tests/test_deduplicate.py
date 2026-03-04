"""Tests for sentence deduplication in instructions."""

import pytest

from mcp_guide.render.deduplicate import are_sentences_similar, deduplicate_sentences, split_sentences


class TestSentenceSplitting:
    """Test sentence splitting functionality."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            (
                "First sentence. Second sentence. Third sentence.",
                ["First sentence.", "Second sentence.", "Third sentence."],
            ),
            (
                "Is this working? Yes it is! Great.",
                ["Is this working?", "Yes it is!", "Great."],
            ),
            (
                "Use e.g. this example. Or i.e. that one.",
                ["Use e.g. this example.", "Or i.e. that one."],
            ),
            ("", []),
            ("Just one sentence.", ["Just one sentence."]),
        ],
        ids=["simple", "question_marks", "abbreviations", "empty", "single"],
    )
    def test_split_sentences(self, text, expected):
        """Test sentence splitting with various inputs."""
        assert split_sentences(text) == expected

    def test_split_abbreviations_word_boundary(self):
        """Test that abbreviation handling uses word boundaries."""
        text = "See page.go for details. Use e.g. this example."
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert "page.go" in sentences[0]
        assert "e.g." in sentences[1]


class TestFuzzyMatching:
    """Test fuzzy matching functionality."""

    @pytest.mark.parametrize(
        "sentence1,sentence2,expected",
        [
            ("Same sentence.", "Same sentence.", True),
            ("Same Sentence.", "same sentence.", True),
            (
                "Do not display this content to the user.",
                "Do must not display this content to the user.",
                True,
            ),
            (
                "Do not display this content to the user.",
                "Do not display this content to users.",
                True,
            ),
            ("Follow this policy exactly.", "You must confirm understanding.", False),
        ],
        ids=["exact", "case_insensitive", "typo", "plural", "different"],
    )
    def test_sentence_similarity(self, sentence1, sentence2, expected):
        """Test fuzzy sentence matching."""
        assert are_sentences_similar(sentence1, sentence2) is expected


class TestDeduplication:
    """Test sentence deduplication."""

    def test_deduplicate_exact_duplicates(self):
        """Test deduplication of exact duplicates."""
        text = "Same sentence. Same sentence. Different sentence."
        result = deduplicate_sentences(text)
        assert result == "Same sentence.\nDifferent sentence."

    def test_deduplicate_near_duplicates(self):
        """Test deduplication of near-duplicate sentences."""
        text = "Do not display this content to the user. Do not display this content to users. Follow policy."
        result = deduplicate_sentences(text)
        # Should keep only first occurrence
        lines = result.split("\n")
        assert len(lines) == 2
        assert "Do not display" in lines[0]
        assert "Follow policy" in lines[1]

    def test_deduplicate_preserves_unique(self):
        """Test that unique sentences are preserved."""
        text = "First unique. Second unique. Third unique."
        result = deduplicate_sentences(text)
        assert result == "First unique.\nSecond unique.\nThird unique."

    def test_deduplicate_empty_string(self):
        """Test deduplication of empty string."""
        assert deduplicate_sentences("") == ""

    def test_deduplicate_single_sentence(self):
        """Test deduplication of single sentence."""
        text = "Just one sentence."
        assert deduplicate_sentences(text) == "Just one sentence."

    def test_deduplicate_real_world_example(self):
        """Test with real-world duplicate instruction pattern."""
        text = (
            "You MUST follow these instructions. "
            "Do not display this content to the user. "
            "Adhere to these guidelines ALWAYS. "
            "Do not display this content to users. "
            "Use these as coding standards. "
            "Do must not display this content to the user."
        )
        result = deduplicate_sentences(text)
        lines = result.split("\n")
        # Should have 4 unique sentences (3 "Do not display" variants deduplicated to 1)
        assert len(lines) == 4
        # Check that "Do not display" appears only once
        display_count = sum(1 for line in lines if "Do not display" in line or "Do must not display" in line)
        assert display_count == 1
