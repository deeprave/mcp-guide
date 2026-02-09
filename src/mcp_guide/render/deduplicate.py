"""Sentence deduplication for instruction text."""

import re
from difflib import SequenceMatcher


def split_sentences(text: str) -> list[str]:
    """Split text into sentences.

    Splits on '.', '!', '?' followed by space or end of string.
    Handles common abbreviations like 'e.g.' and 'i.e.'.

    Args:
        text: Text to split into sentences

    Returns:
        List of sentences with punctuation preserved
    """
    if not text or not text.strip():
        return []

    # Replace common abbreviations temporarily to avoid false splits
    text = text.replace("e.g.", "e~g~")
    text = text.replace("i.e.", "i~e~")
    text = text.replace("etc.", "etc~")

    # Split on sentence-ending punctuation followed by space or end
    sentences = re.split(r"(?<=[.!?])\s+", text)

    # Restore abbreviations and clean up
    sentences = [
        s.replace("e~g~", "e.g.").replace("i~e~", "i.e.").replace("etc~", "etc.").strip()
        for s in sentences
        if s.strip()
    ]

    return sentences


def are_sentences_similar(sent1: str, sent2: str, threshold: float = 0.85) -> bool:
    """Check if two sentences are similar using fuzzy matching.

    Args:
        sent1: First sentence
        sent2: Second sentence
        threshold: Similarity threshold (0.0 to 1.0), default 0.85

    Returns:
        True if sentences are similar enough to be considered duplicates
    """
    # Normalize for comparison (lowercase, strip whitespace)
    norm1 = sent1.lower().strip()
    norm2 = sent2.lower().strip()

    # Exact match after normalization
    if norm1 == norm2:
        return True

    # Fuzzy match using SequenceMatcher
    ratio = SequenceMatcher(None, norm1, norm2).ratio()
    return ratio >= threshold


def deduplicate_sentences(text: str) -> str:
    """Deduplicate sentences in text using fuzzy matching.

    Splits text into sentences, removes duplicates and near-duplicates,
    keeping only the first occurrence of each unique sentence.

    Args:
        text: Text containing potentially duplicate sentences

    Returns:
        Text with deduplicated sentences, one per line
    """
    if not text or not text.strip():
        return ""

    sentences = split_sentences(text)
    if not sentences:
        return ""

    unique_sentences = []
    seen_normalized: list[str] = []

    for sentence in sentences:
        # Check if this sentence is similar to any we've already seen
        is_duplicate = False
        for seen in seen_normalized:
            if are_sentences_similar(sentence, seen):
                is_duplicate = True
                break

        if not is_duplicate:
            unique_sentences.append(sentence)
            seen_normalized.append(sentence)

    return "\n".join(unique_sentences)
