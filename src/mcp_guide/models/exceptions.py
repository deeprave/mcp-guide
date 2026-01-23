"""Exception classes for models."""


class NoProjectError(Exception):
    """Raised when no project or session is available."""

    pass


class CategoryNotFoundError(Exception):
    """Raised when a category is not found in the project."""

    def __init__(self, category_name: str):
        self.category_name = category_name
        super().__init__(f"Category '{category_name}' not found in project")


class CollectionNotFoundError(Exception):
    """Raised when a collection is not found in the project."""

    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        super().__init__(f"Collection '{collection_name}' not found in project")


class ExpressionParseError(Exception):
    """Raised when expression parsing fails."""

    pass


class FileReadError(Exception):
    """Raised when file reading fails."""

    pass
