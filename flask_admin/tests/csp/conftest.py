import secrets

import pytest
from flask_admin.base import Admin


@pytest.fixture
def nonce():
    return secrets.token_urlsafe(32)


@pytest.fixture
def admin(app, babel, nonce):
    def csp_nonce_generator():
        return nonce

    admin = Admin(app, csp_nonce_generator=csp_nonce_generator)
    yield admin
