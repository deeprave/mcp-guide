"""Tests for client-owned export write instructions."""

from mcp_guide.tools.tool_content import _build_export_write_instruction


class TestBuildExportWriteInstruction:
    """Tests for the exact-path export write instruction."""

    def test_create_only_instruction_includes_destination(self) -> None:
        instruction = _build_export_write_instruction(".claude/knowledge/CODEREVIEW.md", False)

        assert "RAW FILE DATA" in instruction
        assert "`.claude/knowledge/CODEREVIEW.md`" in instruction
        assert "create only; do not overwrite if it exists" in instruction
        assert "If the destination file already exists, do not overwrite it" in instruction
        assert "display it to the user" in instruction

    def test_force_instruction_uses_overwrite_wording(self) -> None:
        instruction = _build_export_write_instruction(".codex/knowledge/guidelines.md", True)

        assert "`.codex/knowledge/guidelines.md`" in instruction
        assert "overwrite if it already exists" in instruction
        assert "create only; do not overwrite if it exists" not in instruction
        assert "modification time at or after the write" in instruction
        assert "If the destination file already exists, do not overwrite it" not in instruction
