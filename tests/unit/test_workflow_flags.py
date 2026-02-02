"""Test workflow flag parsing and validation."""

import pytest

from mcp_guide.workflow.flags import parse_workflow_phases, substitute_variables, validate_workflow_file_path


class TestVariableSubstitution:
    """Test variable substitution in workflow flags."""

    def test_substitute_project_name(self):
        """Test {project-name} substitution."""
        result = substitute_variables("{project-name}.yaml", project_name="test-project")
        assert result == "test-project.yaml"

    def test_substitute_project_key(self):
        """Test {project-key} substitution."""
        result = substitute_variables("/tmp/{project-key}.yaml", project_key="test-abc123")
        assert result == "/tmp/test-abc123.yaml"

    def test_substitute_project_hash(self):
        """Test {project-hash} substitution."""
        result = substitute_variables(".{project-hash}.yaml", project_hash="abc123def")
        assert result == ".abc123def.yaml"

    def test_substitute_multiple_variables(self):
        """Test multiple variable substitution."""
        result = substitute_variables(
            "/tmp/{project-name}-{project-hash}.yaml", project_name="test", project_hash="abc123"
        )
        assert result == "/tmp/test-abc123.yaml"

    def test_no_substitution_needed(self):
        """Test string without variables."""
        result = substitute_variables(".guide.yaml")
        assert result == ".guide.yaml"


class TestWorkflowPhases:
    """Test workflow phase parsing."""

    def test_parse_false_disables_workflow(self):
        """Test workflow=false disables tracking."""
        result = parse_workflow_phases(False)
        assert result.enabled is False
        assert result.phases == []

    def test_parse_true_uses_default_phases(self):
        """Test workflow=true uses default sequence."""
        result = parse_workflow_phases(True)
        assert result.enabled is True
        assert result.phases == ["discussion", "planning", "implementation", "check", "review"]

    def test_parse_custom_phases_valid(self):
        """Test parsing custom phase list with valid phases."""
        custom_phases = ["discussion", "planning", "implementation"]
        result = parse_workflow_phases(custom_phases)
        assert result.enabled is True
        assert result.phases == custom_phases

    def test_parse_custom_phases_invalid(self):
        """Test parsing custom phase list with invalid phase."""
        invalid_phases = ["discussion", "invalid-phase", "implementation"]
        with pytest.raises(ValueError, match="Invalid phase name: 'invalid-phase'"):
            parse_workflow_phases(invalid_phases)


class TestWorkflowFileSecurity:
    """Test workflow file path security validation."""

    def test_validate_allowed_relative_path(self):
        """Test validation passes for relative paths in allowed directories."""
        allowed_paths = ["config/"]  # Directory with trailing slash like defaults
        workflow_file = "config/.guide.yaml"  # File in allowed directory

        # Should pass validation for relative path in allowed directory
        result = validate_workflow_file_path(workflow_file, allowed_paths)
        assert result == workflow_file

    def test_validate_rejects_unsafe_path(self):
        """Test validation rejects paths outside allowed directories."""
        from mcp_guide.filesystem.read_write_security import SecurityError

        allowed_paths = ["config/"]
        unsafe_path = "/etc/passwd"

        with pytest.raises(SecurityError, match="Write to absolute path not allowed"):
            validate_workflow_file_path(unsafe_path, allowed_paths)


class TestWorkflowFlagValidation:
    """Test workflow flag validation."""

    def test_workflow_flag_rejects_markers(self):
        """Test workflow flag validator rejects phases with markers."""
        from mcp_guide.workflow.flags import _validate_workflow_flag

        # Should reject phases with prefix marker
        assert _validate_workflow_flag(["discussion", "*implementation"], False) is False

        # Should reject phases with suffix marker
        assert _validate_workflow_flag(["discussion", "check*"], False) is False

        # Should reject phases with both markers
        assert _validate_workflow_flag(["*implementation*"], False) is False

    def test_workflow_flag_accepts_clean_phases(self):
        """Test workflow flag validator accepts clean phase names."""
        from mcp_guide.workflow.flags import _validate_workflow_flag

        # Should accept clean phase names
        assert _validate_workflow_flag(["discussion", "planning", "implementation"], False) is True

        # Should accept boolean
        assert _validate_workflow_flag(True, False) is True
        assert _validate_workflow_flag(False, False) is True

    def test_workflow_flag_rejects_invalid_phases(self):
        """Test workflow flag validator rejects invalid phase names."""
        from mcp_guide.workflow.flags import _validate_workflow_flag

        # Should reject invalid phase name
        assert _validate_workflow_flag(["discussion", "implementation", "invalid_phase"], False) is False

    def test_workflow_flag_requires_mandatory_phases(self):
        """Test workflow flag validator requires discussion and implementation."""
        from mcp_guide.workflow.flags import _validate_workflow_flag

        # Should reject without discussion
        assert _validate_workflow_flag(["planning", "implementation", "check"], False) is False

        # Should reject without implementation
        assert _validate_workflow_flag(["discussion", "planning", "check"], False) is False

        # Should accept with both mandatory phases
        assert _validate_workflow_flag(["discussion", "implementation"], False) is True
        assert _validate_workflow_flag(["discussion", "planning", "implementation", "check", "review"], False) is True


class TestWorkflowConsentValidation:
    """Test workflow-consent flag validation."""

    def test_consent_flag_rejects_boolean(self):
        """Test consent flag validator rejects boolean values."""
        from mcp_guide.workflow.flags import _validate_workflow_consent_flag

        assert _validate_workflow_consent_flag(True, False) is False
        assert _validate_workflow_consent_flag(False, False) is False
        assert _validate_workflow_consent_flag(None, False) is True

    def test_consent_flag_accepts_valid_dict(self):
        """Test consent flag validator accepts valid dict structure."""
        from mcp_guide.workflow.flags import _validate_workflow_consent_flag

        # Valid consent configuration with lists
        consent = {"implementation": ["entry"], "review": ["exit"]}
        assert _validate_workflow_consent_flag(consent, False) is True

        # Valid with both entry and exit
        consent = {"planning": ["entry", "exit"]}
        assert _validate_workflow_consent_flag(consent, False) is True

        # Valid with single string (YAML shorthand)
        consent = {"implementation": "entry", "review": "exit"}
        assert _validate_workflow_consent_flag(consent, False) is True

    def test_consent_flag_rejects_invalid_phase(self):
        """Test consent flag validator rejects invalid phase names."""
        from mcp_guide.workflow.flags import _validate_workflow_consent_flag

        # Invalid phase name
        consent = {"invalid_phase": ["entry"]}
        assert _validate_workflow_consent_flag(consent, False) is False

    def test_consent_flag_rejects_invalid_consent_type(self):
        """Test consent flag validator rejects invalid consent types."""
        from mcp_guide.workflow.flags import _validate_workflow_consent_flag

        # Invalid consent type in list
        consent = {"implementation": ["invalid"]}
        assert _validate_workflow_consent_flag(consent, False) is False

        # Invalid consent type as string
        consent = {"implementation": "invalid"}
        assert _validate_workflow_consent_flag(consent, False) is False

        # Must be string or list, not other types
        consent = {"implementation": 123}
        assert _validate_workflow_consent_flag(consent, False) is False
