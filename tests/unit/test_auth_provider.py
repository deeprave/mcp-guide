"""Behavioural tests for optional authentication-provider loading."""

from contextlib import nullcontext
from importlib.metadata import EntryPoint
from unittest.mock import patch

import pytest


def test_auth_provider_option_selects_named_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI retains a selected provider name without importing it."""
    from mcp_guide.cli import parse_args

    monkeypatch.setattr("sys.argv", ["mcp-guide", "https", "--auth-provider", "example"])

    config = parse_args()

    assert config.auth_provider == "example"


def test_auth_provider_loader_resolves_only_selected_entry_point() -> None:
    """Selecting a provider loads its factory from the dedicated entry-point group."""
    from mcp_guide.auth import load_auth_provider_factory

    selected = EntryPoint(name="example", value="example:factory", group="mcp_guide.auth_providers")
    ignored = EntryPoint(name="other", value="other:factory", group="mcp_guide.auth_providers")
    factory = lambda: object()

    with (
        patch("mcp_guide.auth.entry_points", return_value=[selected, ignored]),
        patch.object(EntryPoint, "load", return_value=factory),
    ):
        loaded = load_auth_provider_factory("example")

    assert loaded is factory


def test_missing_selected_provider_is_a_configuration_error() -> None:
    """A typo cannot silently weaken a configured remote boundary."""
    from mcp_guide.auth import AuthProviderConfigurationError, load_auth_provider_factory

    with patch("mcp_guide.auth.entry_points", return_value=[]):
        with pytest.raises(AuthProviderConfigurationError, match="missing"):
            load_auth_provider_factory("missing")


def test_protected_tools_declare_their_required_scopes() -> None:
    """The public tool registry makes the bounded policy reviewable."""
    import mcp_guide.tools  # noqa: F401
    from mcp_guide.auth import AuthScope
    from mcp_guide.core.tool_decorator import get_tool_registration

    expected = {
        "set_project_flag": AuthScope.USER,
        "set_feature_flag": AuthScope.ADMIN,
        "clone_project": AuthScope.ADMIN,
        "use_project_profile": AuthScope.USER,
        "add_permission_path": AuthScope.ADMIN,
        "remove_permission_path": AuthScope.ADMIN,
        "category_collection_add": AuthScope.USER,
        "category_collection_remove": AuthScope.USER,
        "category_collection_change": AuthScope.USER,
        "category_collection_update": AuthScope.USER,
        "send_file_content": AuthScope.USER,
        "document_remove": AuthScope.USER,
        "document_update": AuthScope.USER,
        "export_content": AuthScope.USER,
        "remove_export": AuthScope.USER,
    }

    assert {name: get_tool_registration(name).metadata.auth_scope for name in expected} == expected
    assert get_tool_registration("set_project").metadata.auth_scope is None
    assert get_tool_registration("switch_project").metadata.auth_scope is None
    assert get_tool_registration("update_documents").metadata.auth_scope is None

    file_content_policy = get_tool_registration("send_file_content").metadata.auth_required
    assert file_content_policy is not None
    assert file_content_policy(type("Args", (), {"category": None})()) is False
    assert file_content_policy(type("Args", (), {"category": "knowledge"})()) is True


@pytest.mark.anyio
async def test_template_auth_context_is_request_specific_and_provider_neutral() -> None:
    """Templates project request scopes without reauthorising each capability."""
    from mcp_guide.auth import (
        AuthScope,
        UserAuthorisation,
        template_auth_context,
    )

    context = await template_auth_context(UserAuthorisation(scopes=frozenset({AuthScope.USER})))

    assert context == {
        "active": True,
        "authenticated": True,
        "user": True,
        "admin": False,
    }

    admin_context = await template_auth_context(UserAuthorisation(scopes=frozenset({AuthScope.ADMIN})))
    assert admin_context == {"active": True, "authenticated": True, "user": True, "admin": True}

    anonymous_context = await template_auth_context(UserAuthorisation(scopes=frozenset()))
    assert anonymous_context == {"active": True, "authenticated": False, "user": False, "admin": False}

    inactive_context = await template_auth_context(None)
    assert inactive_context == {"active": False, "authenticated": True, "user": True, "admin": True}


def test_user_authorisation_rejects_raw_scope_strings() -> None:
    """Provider output must use the public scope enum rather than strings."""
    from mcp_guide.auth import UserAuthorisation

    with pytest.raises(TypeError, match="AuthScope"):
        UserAuthorisation(scopes=frozenset({"user"}))  # type: ignore[arg-type]


@pytest.mark.parametrize("raise_error", [False, True], ids=["normal-exit", "exception-exit"])
def test_authorisation_binding_restores_previous_request_state(raise_error):
    """Nested bindings restore the caller's decision and never leak after exit."""
    from mcp_guide.auth import AuthScope, UserAuthorisation, bind_user_authorisation, current_user_authorisation

    user = UserAuthorisation(scopes=frozenset({AuthScope.USER}))
    admin = UserAuthorisation(scopes=frozenset({AuthScope.ADMIN}))
    assert current_user_authorisation() is None

    with bind_user_authorisation(user):
        assert current_user_authorisation() is user
        expected_exit = pytest.raises(RuntimeError) if raise_error else nullcontext()
        with expected_exit:
            with bind_user_authorisation(admin):
                assert current_user_authorisation() is admin
                if raise_error:
                    raise RuntimeError("Request failed")
        assert current_user_authorisation() is user

    assert current_user_authorisation() is None


@pytest.mark.anyio
async def test_auth_service_starts_provider_and_returns_opaque_decision() -> None:
    """A remote service returns provider scopes without inspecting credentials."""
    from mcp_guide.auth import AuthEvidence, AuthScope, AuthService, UserAuthorisation

    class Provider:
        started = False
        stopped = False

        async def start(self) -> None:
            self.started = True

        async def stop(self) -> None:
            self.stopped = True

        async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
            assert evidence.method == "POST"
            return UserAuthorisation(scopes=frozenset({AuthScope.USER}))

    provider = Provider()
    service = AuthService(lambda: provider)
    evidence = AuthEvidence(headers=((b"authorization", b"Bearer opaque"),), method="POST", path="/mcp")

    await service.start()
    result = await service.authenticate(evidence)
    await service.stop()

    assert result.scopes == frozenset({AuthScope.USER})
    assert provider.started is True
    assert provider.stopped is True


@pytest.mark.anyio
async def test_auth_service_authenticates_each_request() -> None:
    """Guide does not cache provider authorisation state."""
    from mcp_guide.auth import AuthEvidence, AuthScope, AuthService, UserAuthorisation

    class Provider:
        calls = 0

        async def start(self) -> None:
            return None

        async def stop(self) -> None:
            return None

        async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
            self.calls += 1
            return UserAuthorisation(scopes=frozenset({AuthScope.USER}))

    provider = Provider()
    service = AuthService(lambda: provider)
    evidence = AuthEvidence(headers=(), method="POST", path="/mcp")
    await service.start()

    await service.authenticate(evidence)
    await service.authenticate(evidence)

    assert provider.calls == 2


@pytest.mark.anyio
async def test_auth_service_rejects_an_invalid_provider_result() -> None:
    """A provider contract error reaches the transport's failure boundary."""
    from mcp_guide.auth import AuthEvidence, AuthProviderResultError, AuthService

    class Provider:
        async def start(self) -> None:
            return None

        async def stop(self) -> None:
            return None

        async def authenticate(self, evidence: AuthEvidence) -> object:
            return None

    service = AuthService(lambda: Provider())
    await service.start()

    with pytest.raises(AuthProviderResultError, match="invalid authorisation"):
        await service.authenticate(AuthEvidence(headers=(), method="POST", path="/mcp"))


@pytest.mark.anyio
async def test_named_auth_service_defers_entry_point_loading_until_transport_start() -> None:
    """Naming a provider does not import it before the remote transport starts."""
    from mcp_guide.auth import auth_service_for

    class Provider:
        async def start(self) -> None:
            return None

        async def stop(self) -> None:
            return None

        async def authenticate(self, *args):
            raise AssertionError("not used")

    factory = lambda: Provider()
    with patch("mcp_guide.auth.load_auth_provider_factory", return_value=factory) as load:
        service = auth_service_for("example")
        load.assert_not_called()
        await service.start()

    load.assert_called_once_with("example")


@pytest.mark.anyio
async def test_protected_operation_maps_missing_authentication_to_not_authorised_result() -> None:
    """A missing user scope yields a handoff without credential data."""
    from mcp_guide.auth import (
        AuthScope,
        UserAuthorisation,
        scope_authorisation_result,
    )

    result = scope_authorisation_result(
        UserAuthorisation(scopes=frozenset(), handoff="https://identity.example/login"),
        AuthScope.USER,
    )

    assert result is not None
    assert result.error_type == "not_authorised"
    assert result.error_data == {"handoff": "https://identity.example/login"}


@pytest.mark.anyio
async def test_protected_operation_maps_insufficient_access_to_forbidden_result() -> None:
    """Guide applies the declared scope policy without token interpretation."""
    from mcp_guide.auth import (
        AuthScope,
        UserAuthorisation,
        scope_authorisation_result,
    )

    result = scope_authorisation_result(
        UserAuthorisation(scopes=frozenset({AuthScope.USER})),
        AuthScope.ADMIN,
    )

    assert result is not None
    assert result.error_type == "forbidden"
    assert result.error_data is None


@pytest.mark.anyio
async def test_auth_service_rejects_an_invalid_provider_at_startup() -> None:
    """A configured provider missing the runtime protocol fails before serving."""
    from mcp_guide.auth import AuthProviderConfigurationError, AuthService

    with pytest.raises(AuthProviderConfigurationError, match="required protocol"):
        await AuthService(lambda: object()).start()


@pytest.mark.anyio
async def test_auth_service_stops_a_provider_after_partial_start_failure() -> None:
    """A provider is always finalised after its own startup failure."""
    from mcp_guide.auth import AuthService

    class Provider:
        stopped = False

        async def start(self) -> None:
            raise RuntimeError("startup failed")

        async def stop(self) -> None:
            self.stopped = True

        async def authenticate(self, *args):
            raise AssertionError("not used")

    provider = Provider()
    with pytest.raises(RuntimeError, match="startup failed"):
        await AuthService(lambda: provider).start()
    assert provider.stopped is True
