"""Test workflow flag parsing and validation."""

import pytest

from mcp_guide.feature_flags.types import FeatureValue
from mcp_guide.workflow.flags import parse_workflow_phases, substitute_variables


class TestVariableSubstitution:
    """Test variable substitution in workflow flags."""

    @pytest.mark.parametrize(
        "template,kwargs,expected",
        [
            ("{project-name}.yaml", {"project_name": "test-project"}, "test-project.yaml"),
            ("/tmp/{project-key}.yaml", {"project_key": "test-abc123"}, "/tmp/test-abc123.yaml"),
            (".{project-hash}.yaml", {"project_hash": "abc123def"}, ".abc123def.yaml"),
            (
                "/tmp/{project-name}-{project-hash}.yaml",
                {"project_name": "test", "project_hash": "abc123"},
                "/tmp/test-abc123.yaml",
            ),
            (".guide.yaml", {}, ".guide.yaml"),
        ],
        ids=["project_name", "project_key", "project_hash", "multiple_variables", "no_substitution"],
    )
    def test_variable_substitution(self, template, kwargs, expected):
        """Test variable substitution in templates."""
        result = substitute_variables(template, **kwargs)
        assert result == expected


class TestWorkflowPhases:
    """Test workflow phase parsing."""

    def test_parse_false_disables_workflow(self):
        """Test workflow=false disables tracking."""
        result = parse_workflow_phases(False)
        assert result.enabled is False
        assert result.phases == []

    def test_parse_true_uses_default_phases(self):
        """Test workflow=true uses default available and ordered phases."""
        result = parse_workflow_phases(True)
        assert result.enabled is True
        assert result.phases == ["discussion", "exploration", "planning", "implementation", "check", "review"]
        assert result.ordered_phases == ["discussion", "planning", "implementation", "check", "review"]

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

    def test_workflow_flag_invalid_type_returns_false(self):
        """Test workflow flag validator returns False for invalid shapes."""
        from mcp_guide.workflow.flags import _validate_workflow_flag

        assert _validate_workflow_flag({"discussion": "implementation"}, False) is False  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("true", True),
            ("TRUE", True),
            ("enabled", True),
            ("yes", True),
            ("1", True),
            ("false", False),
            ("FALSE", False),
            ("disabled", False),
            ("no", False),
            ("0", False),
        ],
    )
    def test_workflow_normaliser_uses_shared_boolean_like_rules(self, value, expected):
        """Workflow shorthand should use the shared boolean-like coercion."""
        from mcp_guide.workflow.flags import _normalise_workflow_flag

        assert _normalise_workflow_flag(value) == expected

    def test_workflow_file_flag_invalid_type_returns_false(self):
        """Test workflow-file validator returns False for invalid shapes."""
        from mcp_guide.workflow.flags import _validate_workflow_file_flag

        assert _validate_workflow_file_flag({"path": ".guide.yaml"}, False) is False  # type: ignore[arg-type]


class TestWorkflowConsentValidation:
    """Test workflow-consent flag validation."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (True, True),
            (False, True),
            ("true", True),
            ("enabled", True),
            ("1", True),
            ("false", True),
            ("disabled", True),
            ("0", True),
            (None, True),
        ],
        ids=["true", "false", "str_true", "str_enabled", "str_one", "str_false", "str_disabled", "str_zero", "none"],
    )
    def test_consent_flag_accepts_boolean_and_none(self, value, expected):
        """Test consent flag validator accepts boolean-like scalars and None."""
        from mcp_guide.workflow.flags import _validate_workflow_consent_flag

        assert _validate_workflow_consent_flag(value, False) is expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("true", True),
            ("yes", True),
            ("1", True),
            ("false", False),
            ("no", False),
            ("0", False),
        ],
    )
    def test_consent_normaliser_uses_shared_boolean_like_rules(self, value, expected):
        """Workflow consent shorthand should use the shared boolean-like coercion."""
        from mcp_guide.workflow.flags import _normalise_workflow_consent_flag

        assert _normalise_workflow_consent_flag(value) == expected

    def test_consent_flag_accepts_valid_dict(self):
        """Test consent flag validator accepts valid dict structure."""
        from mcp_guide.workflow.flags import _validate_workflow_consent_flag

        # Valid consent configuration with lists
        consent: FeatureValue = {"implementation": ["entry"], "review": ["exit"]}
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
        consent: FeatureValue = {"invalid_phase": ["entry"]}
        assert _validate_workflow_consent_flag(consent, False) is False

    def test_consent_flag_rejects_invalid_consent_type(self):
        """Test consent flag validator rejects invalid consent types."""
        from mcp_guide.workflow.flags import _validate_workflow_consent_flag

        # Invalid consent type in list
        consent: FeatureValue = {"implementation": ["invalid"]}
        assert _validate_workflow_consent_flag(consent, False) is False

        # Invalid consent type as string
        consent = {"implementation": "invalid"}
        assert _validate_workflow_consent_flag(consent, False) is False

        # Must be string or list, not other types
        consent: object = {"implementation": 123}
        assert _validate_workflow_consent_flag(consent, False) is False  # ty: ignore[invalid-argument-type]


class TestStartupInstructionValidation:
    """Test startup-instruction flag validation."""

    def test_startup_instruction_invalid_type_returns_false(self):
        """Test startup-instruction validator returns False for invalid shapes."""
        from mcp_guide.workflow.flags import _validate_startup_instruction_flag

        assert _validate_startup_instruction_flag({"instruction": "run"}, False) is False  # type: ignore[arg-type]
