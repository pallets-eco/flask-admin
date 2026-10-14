"""End-to-end tests for FileAdmin rendered with the Tabler theme."""

import typing as t
from pathlib import Path

from playwright.sync_api import expect
from playwright.sync_api import Page


def test_file_list_renders(page: Page, live_server: dict[str, t.Any]) -> None:
    # Regression test: the Tabler file list template used a missing
    # ``admin_static.get_url`` macro and returned HTTP 500.
    response = page.goto(f"{live_server['url']}/admin/fileadmin/")
    assert response is not None and response.ok
    expect(page.get_by_text("hello.txt")).to_be_visible()


def test_file_upload(page: Page, live_server: dict[str, t.Any], tmp_path: Path) -> None:
    upload_file = tmp_path / "upload.txt"
    upload_file.write_text("uploaded via e2e")
    page.goto(f"{live_server['url']}/admin/fileadmin/upload/")
    page.locator('input[name="upload"]').set_input_files(str(upload_file))
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()
    expect(page.get_by_role("link", name="upload.txt")).to_be_visible()
    assert (live_server["files_dir"] / "upload.txt").is_file()
