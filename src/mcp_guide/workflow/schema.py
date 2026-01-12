"""Workflow state schema definitions."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkflowState(BaseModel):
    """Schema for .guide.yaml workflow state file."""

    phase: str = Field(default="discussion", description="Current workflow phase")
    issue: Optional[str] = Field(default=None, description="Current issue ID or path")
    plan: Optional[str] = Field(default=None, description="Relative path to implementation plan file")
    tracking: Optional[str] = Field(default=None, description="External tracker reference (e.g., 'JIRA PROJ-123')")
    description: Optional[str] = Field(default=None, description="Optional phase context or sub-phase info")
    queue: list[str] = Field(default_factory=list, description="Queued issues in priority order")

    model_config = ConfigDict(
        extra="allow",  # Allow additional fields to be loaded and preserved
    )
