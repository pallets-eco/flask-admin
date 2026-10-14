"""End-to-end tests for model views rendered with the Tabler theme."""

import typing as t

from playwright.sync_api import expect
from playwright.sync_api import Locator
from playwright.sync_api import Page

from flask_admin.tests.e2e.app_factory import Author
from flask_admin.tests.e2e.app_factory import Book
from flask_admin.tests.e2e.app_factory import db


def _base_url(live_server: dict[str, t.Any]) -> str:
    return live_server["url"]


def _author_id(live_server: dict[str, t.Any], name: str) -> int:
    with live_server["app"].app_context():
        return Author.query.filter_by(name=name).first().id


def _book_titles(live_server: dict[str, t.Any]) -> list[str]:
    with live_server["app"].app_context():
        return sorted(book.title for book in Book.query.all())


def _inline_card(page: Page, heading: str) -> Locator:
    return page.locator(".inline-field-list .inline-field", has_text=heading)


def test_admin_home_renders(page: Page, live_server: dict[str, t.Any]) -> None:
    response = page.goto(f"{_base_url(live_server)}/admin/")
    assert response is not None and response.ok
    expect(page.get_by_role("link", name="Author")).to_be_visible()
    expect(page.get_by_role("link", name="Files")).to_be_visible()


def test_model_list_renders_rows(page: Page, live_server: dict[str, t.Any]) -> None:
    # Regression test: the Tabler list template used a missing
    # ``admin_static.get_url`` macro and returned HTTP 500.
    response = page.goto(f"{_base_url(live_server)}/admin/author/")
    assert response is not None and response.ok
    expect(page.get_by_text("Jane Austen")).to_be_visible()
    expect(page.get_by_text("Charles Dickens")).to_be_visible()
    # NOTE: located by CSS because the tab-bar "Create" link and the header
    # "Create" button share an accessible name (icon fonts render as text).
    expect(page.locator('a.btn[title="Create New Record"]')).to_be_visible()


def test_model_list_search_filters_rows(
    page: Page, live_server: dict[str, t.Any]
) -> None:
    page.goto(f"{_base_url(live_server)}/admin/author/")
    page.locator('input[name="search"]').fill("Dickens")
    with page.expect_navigation():
        page.get_by_role("button", name="Search", exact=True).click()
    expect(page.get_by_text("Charles Dickens")).to_be_visible()
    expect(page.get_by_text("Jane Austen")).not_to_be_visible()


def test_model_details_renders(page: Page, live_server: dict[str, t.Any]) -> None:
    author_id = _author_id(live_server, "Jane Austen")
    response = page.goto(
        f"{_base_url(live_server)}/admin/author/details/?id={author_id}"
    )
    assert response is not None and response.ok
    expect(page.get_by_text("Jane Austen")).to_be_visible()


def test_create_author_with_inline_book(
    page: Page, live_server: dict[str, t.Any]
) -> None:
    page.goto(f"{_base_url(live_server)}/admin/author/new/")
    page.get_by_label("Name *").fill("Virginia Woolf")
    page.get_by_role("button", name="Add Books").click()
    new_card = _inline_card(page, "New Books")
    expect(new_card).to_be_visible()
    # Found by label: the add-row JavaScript must rewrite ``<label for>``
    # to match the cloned input's id.
    new_card.get_by_label("Title *").fill("Mrs Dalloway")
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()
    expect(page.get_by_text("Virginia Woolf")).to_be_visible()
    assert _book_titles(live_server) == ["Mrs Dalloway", "Pride and Prejudice"]


def test_create_requires_name(page: Page, live_server: dict[str, t.Any]) -> None:
    page.goto(f"{_base_url(live_server)}/admin/author/new/")
    # Bypass browser-native validation to exercise the server-side path.
    # A validation failure re-renders the form, so no navigation happens.
    page.eval_on_selector("#name", "el => el.removeAttribute('required')")
    page.get_by_role("button", name="Save", exact=True).click()
    expect(page.get_by_text("This field is required.")).to_be_visible()
    assert page.url.endswith("/admin/author/new/")
    with live_server["app"].app_context():
        assert Author.query.count() == 2


def test_edit_shows_existing_inline_entry(
    page: Page, live_server: dict[str, t.Any]
) -> None:
    author_id = _author_id(live_server, "Jane Austen")
    response = page.goto(f"{_base_url(live_server)}/admin/author/edit/?id={author_id}")
    assert response is not None and response.ok
    card = _inline_card(page, "Books #1")
    expect(card).to_be_visible()
    expect(card.locator('input[type="text"]')).to_have_value("Pride and Prejudice")
    expect(page.get_by_label("Delete?")).to_be_visible()


def test_edit_can_add_inline_entry(page: Page, live_server: dict[str, t.Any]) -> None:
    author_id = _author_id(live_server, "Jane Austen")
    page.goto(f"{_base_url(live_server)}/admin/author/edit/?id={author_id}")
    page.get_by_role("button", name="Add Books").click()
    new_card = _inline_card(page, "New Books")
    expect(new_card).to_be_visible()
    # The remove control is icon-only, so it must expose an accessible name.
    # Asserted by attribute: without icon fonts loaded the link has no
    # rendered size, so a visibility assertion would be environment-bound.
    expect(new_card.locator("a.inline-remove-field")).to_have_attribute(
        "aria-label", "Remove"
    )
    new_card.get_by_label("Title *").fill("Emma")
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()
    assert _book_titles(live_server) == ["Emma", "Pride and Prejudice"]


def test_edit_can_delete_inline_entry(
    page: Page, live_server: dict[str, t.Any]
) -> None:
    author_id = _author_id(live_server, "Jane Austen")
    page.goto(f"{_base_url(live_server)}/admin/author/edit/?id={author_id}")
    page.get_by_label("Delete?").check()
    with page.expect_navigation():
        page.get_by_role("button", name="Save", exact=True).click()
    assert _book_titles(live_server) == []
    with live_server["app"].app_context():
        assert Author.query.filter_by(name="Jane Austen").count() == 1


def test_model_list_sorting_toggles_order(
    page: Page, live_server: dict[str, t.Any]
) -> None:
    # NOTE: asserts toggling, not absolute direction: first-click direction
    # is upstream flask-admin behavior and identical under Bootstrap.
    page.goto(f"{_base_url(live_server)}/admin/author/")
    rows = page.locator("table.model-list tbody tr")
    first_row_default = " ".join(rows.nth(0).inner_text().split())
    name_header_link = page.locator("th.column-header", has_text="Name").locator("a")
    name_header_link.click()
    page.wait_for_url("**/admin/author/**")
    assert " ".join(rows.nth(0).inner_text().split()) != first_row_default
    name_header_link.click()
    page.wait_for_url("**/admin/author/**")
    expect(rows.nth(0)).to_contain_text("Jane Austen")


def test_model_list_pagination(page: Page, live_server: dict[str, t.Any]) -> None:
    with live_server["app"].app_context():
        for index in range(25):
            db.session.add(Author(name=f"Bulk Author {index:02d}"))
        db.session.commit()
    page.goto(f"{_base_url(live_server)}/admin/author/")
    rows = page.locator("table.model-list tbody tr")
    expect(rows).to_have_count(20)
    first_row_page_one = rows.nth(0).inner_text()
    with page.expect_navigation():
        page.locator("ul.pagination").get_by_role("link", name="2", exact=True).click()
    expect(rows).to_have_count(7)
    assert rows.nth(0).inner_text() != first_row_page_one


def test_model_list_filter_narrows_results(
    page: Page, live_server: dict[str, t.Any]
) -> None:
    page.goto(f"{_base_url(live_server)}/admin/author/")
    page.get_by_role("button", name="Add Filter").click()
    page.locator("a.filter", has_text="Name").click()
    page.locator("input.filter-val").fill("Dickens")
    with page.expect_navigation():
        page.get_by_role("button", name="Apply", exact=True).click()
    expect(page.get_by_text("Charles Dickens")).to_be_visible()
    expect(page.get_by_text("Jane Austen")).not_to_be_visible()
