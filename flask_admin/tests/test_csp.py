import secrets
import typing as t

import pytest
from bs4 import BeautifulSoup
from flask import Flask

from flask_admin import Admin


@pytest.fixture
def nonce() -> str:
    return secrets.token_urlsafe(32)


@pytest.fixture
def admin(
    app: Flask, babel: object | None, nonce: str
) -> t.Generator[Admin, None, None]:
    def csp_nonce_generator() -> str:
        return nonce

    admin = Admin(app, csp_nonce_generator=csp_nonce_generator)
    yield admin


def test_csp_nonces_injected(app: Flask, admin: Admin, nonce: str) -> None:
    client = app.test_client()
    rv = client.get("/admin/")
    assert rv.status_code == 200

    soup = BeautifulSoup(rv.data, "html.parser")

    scripts = soup.select("script")
    assert len(scripts) == 9
    for tag in scripts:
        assert tag.attrs["nonce"] == nonce

    styles = soup.select("style")
    assert len(styles) == 0
    for tag in styles:
        assert tag.attrs["nonce"] == nonce
