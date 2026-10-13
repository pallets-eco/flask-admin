"""End-to-end tests for the Tabler theme chrome (theme switcher)."""

import typing as t

from playwright.sync_api import expect
from playwright.sync_api import Page


def test_theme_switcher_links(page: Page, live_server: dict[str, t.Any]) -> None:
    # Located by CSS: the inactive toggle is ``display: none`` and therefore
    # absent from the accessibility tree by design.
    page.goto(f"{live_server['url']}/admin/author/")
    expect(page.locator('a[href="?theme=dark"]')).to_have_attribute(
        "aria-label", "Enable dark mode"
    )
    expect(page.locator('a[href="?theme=light"]')).to_have_attribute(
        "aria-label", "Enable light mode"
    )


def test_theme_switcher_toggles_theme(
    page: Page, live_server: dict[str, t.Any]
) -> None:
    # The ``?theme=`` switcher links are wired to ``tabler_theme.js``, which
    # applies the choice as ``data-bs-theme`` on ``<html>`` and persists it.
    page.goto(f"{live_server['url']}/admin/author/")
    with page.expect_navigation():
        page.locator('a[href="?theme=dark"]').click()
    expect(page.locator("html")).to_have_attribute("data-bs-theme", "dark")
    with page.expect_navigation():
        page.locator('a[href="?theme=light"]').click()
    expect(page.locator("html")).to_have_attribute("data-bs-theme", "light")
