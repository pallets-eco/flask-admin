import secrets
import typing as t

import pytest
from flask import Flask
from flask_admin.base import Admin


@pytest.fixture
def babel(app: Flask) -> t.Generator[object | None, None, None]:
    try:
        from flask_babel import Babel
    except ImportError:
        yield None
        return

    yield Babel(app)


@pytest.fixture
def nonce() -> str:
    return secrets.token_urlsafe(32)


@pytest.fixture
def admin(
    app: Flask, babel: t.Any | None, nonce: str
) -> t.Generator[Admin, t.Any, None]:
    def csp_nonce_generator() -> str:
        return nonce

    admin = Admin(app, csp_nonce_generator=csp_nonce_generator)
    yield admin
