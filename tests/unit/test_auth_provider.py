"""Behavioural tests for the provider-neutral authentication boundary."""

from contextlib import nullcontext
from importlib.metadata import EntryPoint
from typing import cast
from unittest.mock import patch

import pytest


class TestProviderLoading:
    def test_auth_provider_option_selects_named_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The CLI retains a selected provider name without importing it."""
        from mcp_guide.cli import parse_args

        monkeypatch.setattr("sys.argv", ["mcp-guide", "https", "--auth-provider", "example"])

        config = parse_args()

        assert config.auth_provider == "example"

    def test_auth_provider_loader_resolves_only_selected_entry_point(self) -> None:
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

    def test_missing_selected_provider_is_a_configuration_error(self) -> None:
        """A typo cannot silently weaken a configured remote boundary."""
        from mcp_guide.auth import AuthProviderConfigurationError, load_auth_provider_factory

        with patch("mcp_guide.auth.entry_points", return_value=[]):
            with pytest.raises(AuthProviderConfigurationError, match="missing"):
                load_auth_provider_factory("missing")

    def test_protected_tools_declare_their_required_scopes(self) -> None:
        """The public tool registry makes the bounded policy reviewable."""
        import mcp_guide.tools  # noqa: F401
        from mcp_guide.auth import AuthScope
        from mcp_guide.core.tool_decorator import get_tool_registration

        def registration(name: str):
            result = get_tool_registration(name)
            assert result is not None
            return result

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
        }

        assert {name: registration(name).metadata.auth_scope for name in expected} == expected
        assert registration("set_project").metadata.auth_scope is None
        assert registration("switch_project").metadata.auth_scope is None
        assert registration("update_documents").metadata.auth_scope is None

        file_content_policy = registration("send_file_content").metadata.auth_required
        assert file_content_policy is not None
        assert file_content_policy(type("Args", (), {"category": None})()) is False
        assert file_content_policy(type("Args", (), {"category": "knowledge"})()) is True


class TestAuthorisationSemantics:
    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("scopes", "expected"),
        [
            (frozenset({"user"}), {"active": True, "authenticated": True, "user": True, "admin": False}),
            (frozenset({"admin"}), {"active": True, "authenticated": True, "user": True, "admin": True}),
            (frozenset(), {"active": True, "authenticated": False, "user": False, "admin": False}),
            (None, {"active": False, "authenticated": True, "user": True, "admin": True}),
        ],
        ids=["user", "admin", "anonymous", "no-provider"],
    )
    async def test_template_auth_context_projects_request_access(
        self,
        scopes: frozenset[str] | None,
        expected: dict[str, bool],
    ) -> None:
        """Templates receive request-local access predicates, not provider data."""
        from mcp_guide.auth import AuthScope, UserAuthorisation, template_auth_context

        authorisation = (
            None if scopes is None else UserAuthorisation(scopes=frozenset(AuthScope(scope) for scope in scopes))
        )

        assert await template_auth_context(authorisation) == expected

    def test_user_authorisation_rejects_raw_scope_strings(self) -> None:
        """Provider output must use the public scope enum rather than strings."""
        from mcp_guide.auth import AuthScope, UserAuthorisation

        with pytest.raises(TypeError, match="AuthScope"):
            UserAuthorisation(scopes=cast(frozenset[AuthScope], frozenset({"user"})))

    @pytest.mark.parametrize("raise_error", [False, True], ids=["normal-exit", "exception-exit"])
    def test_authorisation_binding_restores_previous_request_state(self, raise_error: bool) -> None:
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

    @pytest.mark.parametrize(
        ("scopes", "handoff", "required_scope", "error_type", "error_data"),
        [
            (
                frozenset(),
                "https://identity.example/login",
                "user",
                "not_authorised",
                {"handoff": "https://identity.example/login"},
            ),
            (frozenset({"user"}), None, "admin", "forbidden", None),
        ],
        ids=["missing-authentication", "insufficient-scope"],
    )
    def test_protected_operation_maps_authorisation_results(
        self,
        scopes: frozenset[str],
        handoff: str | None,
        required_scope: str,
        error_type: str,
        error_data: dict[str, str] | None,
    ) -> None:
        """Guide returns its declared error result without interpreting credentials."""
        from mcp_guide.auth import AuthScope, UserAuthorisation, scope_authorisation_result

        result = scope_authorisation_result(
            UserAuthorisation(scopes=frozenset(AuthScope(scope) for scope in scopes), handoff=handoff),
            AuthScope(required_scope),
        )

        assert result is not None
        assert result.error_type == error_type
        assert result.error_data == error_data


class TestAuthService:
    @pytest.mark.anyio
    async def test_starts_provider_and_returns_opaque_decision(self) -> None:
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
    async def test_concurrent_authentication_waits_for_provider_startup(self) -> None:
        """A second protected request cannot call a provider still starting."""
        import asyncio

        from mcp_guide.auth import AuthEvidence, AuthScope, AuthService, UserAuthorisation

        start_entered = asyncio.Event()
        release_start = asyncio.Event()
        start_finished = asyncio.Event()

        class Provider:
            async def start(self) -> None:
                start_entered.set()
                await release_start.wait()
                start_finished.set()

            async def stop(self) -> None:
                return None

            async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
                assert start_finished.is_set()
                return UserAuthorisation(scopes=frozenset({AuthScope.USER}))

        service = AuthService(Provider)
        evidence = AuthEvidence(headers=(), method="POST", path="/mcp")
        first = asyncio.create_task(service.authenticate(evidence))
        await start_entered.wait()
        second = asyncio.create_task(service.authenticate(evidence))
        await asyncio.sleep(0)
        assert not second.done()

        release_start.set()
        results = await asyncio.gather(first, second)

        assert [result.scopes for result in results] == [frozenset({AuthScope.USER})] * 2

    @pytest.mark.anyio
    async def test_rejects_an_invalid_provider_result(self) -> None:
        """A provider contract error reaches the transport's failure boundary."""
        from mcp_guide.auth import AuthEvidence, AuthProviderResultError, AuthService, UserAuthorisation

        class Provider:
            async def start(self) -> None:
                return None

            async def stop(self) -> None:
                return None

            async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
                return cast(UserAuthorisation, None)

        service = AuthService(lambda: Provider())
        await service.start()

        with pytest.raises(AuthProviderResultError, match="invalid authorisation"):
            await service.authenticate(AuthEvidence(headers=(), method="POST", path="/mcp"))

    @pytest.mark.anyio
    async def test_named_service_defers_entry_point_loading_until_a_protected_operation(self) -> None:
        """Naming a provider does not import it until a protected operation needs it."""
        from mcp_guide.auth import AuthEvidence, AuthScope, UserAuthorisation, auth_service_for

        class Provider:
            async def start(self) -> None:
                return None

            async def stop(self) -> None:
                return None

            async def authenticate(self, evidence):
                return UserAuthorisation(scopes=frozenset({AuthScope.USER}))

        factory = lambda: Provider()
        with patch("mcp_guide.auth.load_auth_provider_factory", return_value=factory) as load:
            service = auth_service_for("example")
            load.assert_not_called()
            await service.authenticate(AuthEvidence(headers=(), method="POST", path="/mcp"))

        load.assert_called_once_with("example")

    @pytest.mark.anyio
    async def test_rejects_an_invalid_provider_at_startup(self) -> None:
        """A configured provider missing the runtime protocol fails before serving."""
        from mcp_guide.auth import AuthProviderConfigurationError, AuthProviderFactory, AuthService

        with pytest.raises(AuthProviderConfigurationError, match="required protocol"):
            await AuthService(cast(AuthProviderFactory, lambda: object())).start()

    @pytest.mark.anyio
    async def test_stops_a_provider_after_partial_start_failure(self) -> None:
        """A provider is always finalised after its own startup failure."""
        from mcp_guide.auth import AuthEvidence, AuthService, UserAuthorisation

        class Provider:
            stopped = False

            async def start(self) -> None:
                raise RuntimeError("startup failed")

            async def stop(self) -> None:
                self.stopped = True

            async def authenticate(self, evidence: AuthEvidence) -> UserAuthorisation:
                raise AssertionError("not used")

        provider = Provider()
        with pytest.raises(RuntimeError, match="startup failed"):
            await AuthService(lambda: provider).start()
        assert provider.stopped is True
