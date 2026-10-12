"""End-to-end tests for FileAdmin rendered with the Tabler theme."""

import typing as t

from playwright.sync_api import expect
from playwright.sync_api import Page


def test_file_list_renders(page: Page, live_server: dict[str, t.Any]) -> None:
    # Regression test: the Tabler file list template used a missing
    # ``admin_static.get_url`` macro and returned HTTP 500.
    response = page.goto(f"{live_server['url']}/admin/fileadmin/")
    assert response is not None and response.ok
    expect(page.get_by_text("hello.txt")).to_be_visible()
