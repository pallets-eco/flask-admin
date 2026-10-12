"""Shared fixtures for Tabler-theme end-to-end tests."""

import threading
import typing as t

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import Browser
from playwright.sync_api import Page
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from flask_admin.tests.e2e.app_factory import Author
from flask_admin.tests.e2e.app_factory import Book
from flask_admin.tests.e2e.app_factory import create_app
from flask_admin.tests.e2e.app_factory import db

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="session")
def live_server(
    tmp_path_factory: pytest.TempPathFactory,
) -> t.Generator[dict[str, t.Any], None, None]:
    workdir = tmp_path_factory.mktemp("tabler-e2e")
    app = create_app(workdir)
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield {
        "app": app,
        "url": f"http://127.0.0.1:{server.server_address[1]}",
        "files_dir": workdir / "files",
    }
    server.shutdown()
    thread.join(timeout=10)


@pytest.fixture(autouse=True)
def seeded_database(
    live_server: dict[str, t.Any],
) -> t.Generator[dict[str, t.Any], None, None]:
    app = live_server["app"]
    with app.app_context():
        db.drop_all()
        db.create_all()
        author = Author(name="Jane Austen")
        db.session.add(author)
        db.session.add(Book(title="Pride and Prejudice", author=author))
        db.session.add(Author(name="Charles Dickens"))
        db.session.commit()

    files_dir = live_server["files_dir"]
    for child in files_dir.iterdir():
        if child.is_file():
            child.unlink()
    (files_dir / "hello.txt").write_text("hello e2e")

    yield live_server


@pytest.fixture(scope="session")
def browser() -> t.Generator[Browser, None, None]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture()
def page(browser: Browser) -> t.Generator[Page, None, None]:
    page = browser.new_page()
    yield page
    page.close()
