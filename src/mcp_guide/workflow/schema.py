"""Workflow state schema definitions."""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

WORK_PHRASE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class WorkflowState(BaseModel):
    """Schema for .guide.yaml workflow state file."""

    phase: str = Field(default="discussion", description="Current workflow phase")
    issue: Optional[str] = Field(
        default=None,
        description="Dash-delimited, filesystem-friendly phrase identifying the current work",
    )
    plan: Optional[str] = Field(default=None, description="Relative path to implementation plan file")
    tracking: Optional[str] = Field(default=None, description="External tracker reference (e.g., 'JIRA PROJ-123')")
    description: Optional[str] = Field(default=None, description="Optional phase context or sub-phase info")
    queue: list[str] = Field(default_factory=list, description="Queued issues in priority order")
    worktree: Optional[str] = Field(default=None, description="Guide worktree label for this workflow state")

    model_config = ConfigDict(
        extra="allow",  # Allow additional fields to be loaded and preserved
    )

    @field_validator("issue")
    @classmethod
    def validate_issue(cls, value: str | None) -> str | None:
        """Require a safe, portable identifier for the current work item."""
        if value is not None and not WORK_PHRASE_PATTERN.fullmatch(value):
            raise ValueError("must be a lowercase dash-delimited work phrase without punctuation or whitespace")
        return value

    @field_validator("queue")
    @classmethod
    def validate_queue(cls, values: list[str]) -> list[str]:
        """Require queued work items to use the same safe identifier format."""
        invalid = [value for value in values if not WORK_PHRASE_PATTERN.fullmatch(value)]
        if invalid:
            raise ValueError("entries must be lowercase dash-delimited work phrases without punctuation or whitespace")
        return values
