import secrets
import typing as t

import pytest
from flask import Flask
from flask_admin.base import Admin


@pytest.fixture
def admin(app: Flask, babel: t.Any | None) -> t.Generator[Admin, t.Any, None]:
    token = secrets.token_urlsafe(32)

    def csp_nonce_generator() -> str:
        return token

    admin = Admin(app, csp_nonce_generator=csp_nonce_generator)
    yield admin
