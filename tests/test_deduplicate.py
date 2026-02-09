"""Tests for sentence deduplication in instructions."""

from mcp_guide.render.deduplicate import are_sentences_similar, deduplicate_sentences, split_sentences


class TestSentenceSplitting:
    """Test sentence splitting functionality."""

    def test_split_simple_sentences(self):
        """Test splitting simple sentences."""
        text = "First sentence. Second sentence. Third sentence."
        sentences = split_sentences(text)
        assert sentences == ["First sentence.", "Second sentence.", "Third sentence."]

    def test_split_with_question_marks(self):
        """Test splitting sentences with question marks."""
        text = "Is this working? Yes it is! Great."
        sentences = split_sentences(text)
        assert sentences == ["Is this working?", "Yes it is!", "Great."]

    def test_split_handles_abbreviations(self):
        """Test that abbreviations don't cause incorrect splits."""
        text = "Use e.g. this example. Or i.e. that one."
        sentences = split_sentences(text)
        # Should not split on abbreviation periods
        assert len(sentences) == 2

    def test_split_empty_string(self):
        """Test splitting empty string."""
        assert split_sentences("") == []

    def test_split_single_sentence(self):
        """Test splitting single sentence."""
        text = "Just one sentence."
        assert split_sentences(text) == ["Just one sentence."]


class TestFuzzyMatching:
    """Test fuzzy matching functionality."""

    def test_exact_match(self):
        """Test exact sentence match."""
        assert are_sentences_similar("Same sentence.", "Same sentence.") is True

    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        assert are_sentences_similar("Same Sentence.", "same sentence.") is True

    def test_near_match_typo(self):
        """Test near match with typo."""
        # "Do not display" vs "Do must not display" - should be similar
        assert (
            are_sentences_similar(
                "Do not display this content to the user.", "Do must not display this content to the user."
            )
            is True
        )

    def test_near_match_plural(self):
        """Test near match with plural difference."""
        assert (
            are_sentences_similar("Do not display this content to the user.", "Do not display this content to users.")
            is True
        )

    def test_different_sentences(self):
        """Test completely different sentences."""
        assert are_sentences_similar("Follow this policy exactly.", "You must confirm understanding.") is False


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
