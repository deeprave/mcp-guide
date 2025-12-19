"""URI parsing utility for guide:// scheme."""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class GuideUri:
    """Parsed guide:// URI components."""

    collection: str
    document: Optional[str] = None


def parse_guide_uri(uri: str) -> GuideUri:
    """Parse guide:// URI into components.

    Args:
        uri: URI string to parse (e.g., "guide://lang/python")

    Returns:
        GuideUri with collection and optional document

    Raises:
        ValueError: If URI scheme is not "guide" or URI is malformed
    """
    parsed = urlparse(uri)

    # Validate scheme
    if parsed.scheme != "guide":
        raise ValueError(f"Invalid URI scheme: expected 'guide', got '{parsed.scheme}'")

    # Extract collection from netloc (host part)
    collection = parsed.netloc
    if not collection:
        raise ValueError("URI must specify a collection")

    # Extract document from path (remove leading slash)
    document = None
    if parsed.path and parsed.path != "/":
        document = parsed.path.lstrip("/")

    return GuideUri(collection=collection, document=document)
