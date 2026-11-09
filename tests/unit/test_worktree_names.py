"""Tests for Guide-issued linked-worktree labels."""

from mcp_guide.worktree_names import allocate_worktree_name


def test_allocate_worktree_name_avoids_existing_context_entries(monkeypatch):
    monkeypatch.setattr("mcp_guide.worktree_names.secrets.choice", lambda candidates: candidates[0])

    name = allocate_worktree_name({"brisk-badger", "brisk-falcon"})

    assert name == "brisk-lizard"
