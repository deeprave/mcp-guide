"""Resolve the configured handoff context target for one project."""

from dataclasses import dataclass
from pathlib import PurePosixPath

from mcp_guide.feature_flags.types import FeatureValueLike, to_raw_feature_value
from mcp_guide.feature_flags.validators import coerce_boolean_like, normalise_handoff_context_target
from mcp_guide.filesystem.read_write_security import ReadWriteSecurityPolicy, SecurityError


@dataclass(frozen=True)
class HandoffContext:
    """One resolved handoff-context delivery target."""

    target: str | None
    format: str | None
    eligible: bool


def resolve_handoff_context(
    value: FeatureValueLike | None,
    *,
    documents_path: str,
    allowed_write_paths: list[str],
) -> HandoffContext:
    """Resolve a configured project-relative handoff target and its eligibility."""
    if value is None:
        return HandoffContext(target=None, format=None, eligible=False)
    raw = to_raw_feature_value(value)
    boolean = coerce_boolean_like(raw)
    if boolean is False:
        return HandoffContext(target=None, format=None, eligible=False)
    if boolean is True:
        configured_target = "context.json"
        target = str(PurePosixPath(documents_path) / configured_target)
    elif isinstance(raw, str):
        configured_target = normalise_handoff_context_target(raw)
        if configured_target is None:
            return HandoffContext(target=None, format=None, eligible=False)
        target_path = PurePosixPath(configured_target)
        target = (
            str(PurePosixPath(documents_path) / target_path)
            if target_path.parent == PurePosixPath(".")
            else str(target_path)
        )
    else:
        return HandoffContext(target=None, format=None, eligible=False)

    try:
        ReadWriteSecurityPolicy(write_allowed_paths=allowed_write_paths).validate_write_path(target)
    except SecurityError:
        eligible = False
    else:
        eligible = True

    return HandoffContext(target=target, format=_format_for_target(target), eligible=eligible)


def _format_for_target(target: str) -> str:
    """Return the requested handoff format implied by a target extension."""
    extension = PurePosixPath(target).suffix.lower()
    return {".json": "JSON", ".md": "Markdown", ".txt": "plain text"}.get(
        extension, extension.removeprefix(".").upper() or "text"
    )
