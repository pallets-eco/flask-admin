import typing as t

from flask import Flask
from flask import request
from flask.blueprints import Blueprint as FlaskBlueprint
from flask.blueprints import BlueprintSetupState as FlaskBlueprintSetupState

try:
    from flask.sansio.app import App  # Flask >3.0
except ImportError:
    from flask import Flask as App  # Flask < 3.0
from flask.typing import RouteCallable

from flask_admin.consts import ADMIN_ROUTES_HOST_VARIABLE
from flask_admin.consts import ADMIN_ROUTES_HOST_VARIABLE_NAME


class _BlueprintSetupStateWithHostSupport(FlaskBlueprintSetupState):
    """Adds the ability to set a hostname on all routes when registering the
    blueprint.
    """

    def __init__(
        self,
        blueprint: FlaskBlueprint,
        app: App,
        options: t.Any,
        first_registration: bool,
    ) -> None:
        super().__init__(blueprint, app, options, first_registration)
        self.host = self.options.get("host")

    def add_url_rule(
        self,
        rule: str,
        endpoint: str | None = None,
        view_func: RouteCallable | None = None,
        **options: t.Any,
    ) -> None:
        # Ensure that every route registered by this blueprint has the host parameter
        options.setdefault("host", self.host)
        super().add_url_rule(rule, endpoint, view_func, **options)


class _BlueprintWithHostSupport(FlaskBlueprint):
    def make_setup_state(
        self, app: App, options: t.Any, first_registration: bool = False
    ) -> _BlueprintSetupStateWithHostSupport:
        return _BlueprintSetupStateWithHostSupport(
            self, app, options, first_registration
        )

    def attach_url_defaults_and_value_preprocessor(self, app: Flask, host: str) -> None:
        if host != ADMIN_ROUTES_HOST_VARIABLE:
            return

        # Automatically inject `admin_routes_host` into `url_for` calls on admin
        # endpoints.
        @self.url_defaults
        def inject_admin_routes_host_if_required(
            endpoint: str, values: dict[str, t.Any]
        ) -> None:
            if app.url_map.is_endpoint_expecting(
                endpoint, ADMIN_ROUTES_HOST_VARIABLE_NAME
            ):
                values.setdefault(ADMIN_ROUTES_HOST_VARIABLE_NAME, request.host)

        # Automatically strip `admin_routes_host` from the endpoint values so
        # that the view methods don't receive that parameter, as it's not actually
        # required by any of them.
        @self.url_value_preprocessor
        def strip_admin_routes_host_from_static_endpoint(
            endpoint: str | None, values: dict[str, t.Any] | None
        ) -> None:
            if (
                endpoint
                and values
                and app.url_map.is_endpoint_expecting(
                    endpoint, ADMIN_ROUTES_HOST_VARIABLE_NAME
                )
            ):
                values.pop(ADMIN_ROUTES_HOST_VARIABLE_NAME, None)
