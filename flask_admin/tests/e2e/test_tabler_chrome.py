"""End-to-end tests for the Tabler theme chrome (theme switcher)."""

import typing as t

from playwright.sync_api import expect
from playwright.sync_api import Page


def test_theme_switcher_links(page: Page, live_server: dict[str, t.Any]) -> None:
    # Asserts the switcher wiring. NOTE: the linked ``demo-theme.js`` is not
    # shipped in the ``@tabler/core`` NPM package, so the toggle has no
    # effect until theme switching is implemented (no 404-free script).
    # Located by CSS: the inactive toggle is ``display: none`` and therefore
    # absent from the accessibility tree by design.
    page.goto(f"{live_server['url']}/admin/author/")
    expect(page.locator('a[href="?theme=dark"]')).to_have_attribute(
        "aria-label", "Enable dark mode"
    )
    expect(page.locator('a[href="?theme=light"]')).to_have_attribute(
        "aria-label", "Enable light mode"
    )
