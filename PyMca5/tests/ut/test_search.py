import pytest

from pytestqt.qtbot import QtBot
from tiled.client.base import BaseClient
from tiled.queries import FullText, Key, Regex

from PyMca5.PyMcaGui.io.QTiledSearch import QTiledSearchWidget
from PyMca5.PyMcaGui.io.TiledRunSelector import TiledRunSelector


def test_init(qtbot: QtBot, tiled_client_run_selector_model: TiledRunSelector):
    """Can create a QTiledSearchWidget object."""
    QTiledSearchWidget(model=tiled_client_run_selector_model)


def test_render(qtbot: QtBot, tiled_client_run_selector_model: TiledRunSelector):
    """Can render a QTiledSearchWidget window."""
    search = QTiledSearchWidget(model=tiled_client_run_selector_model)
    search.show()
    qtbot.addWidget(search)


def test_regex_checkbox_disables_key_field(qtbot: QtBot):
    """Checked RegEx checkbox should disable key and FullText elements."""
    search = QTiledSearchWidget(model=None)
    search.show()
    qtbot.addWidget(search)
    # Assert all these elemnts start enabled
    assert all(
        [
            element.isEnabled()
            for element in [
                search.key_label,
                search.key_text_edit,
                search.full_text_checkbox,
            ]
        ]
    )

    search.regex_checkbox.click()

    # None of these elements should be enabled now
    assert not all(
        [
            element.isEnabled()
            for element in [
                search.key_label,
                search.key_text_edit,
                search.full_text_checkbox,
            ]
        ]
    )


def test_fulltext_checkbox_hides_regex_checkbox(qtbot: QtBot):
    """Checked FullText checkbox should hide RegEx checkbox."""
    search = QTiledSearchWidget(model=None)
    search.show()
    qtbot.addWidget(search)
    # RegEx checkbox should be visible
    # full text advice label should not be visible
    assert search.regex_checkbox.isVisible() == True
    assert search.full_text_advice.isVisible() == False

    search.full_text_checkbox.click()

    # RegEx checkbox should not be visible
    # full text advice label should be visible
    assert search.regex_checkbox.isVisible() == False
    assert search.full_text_advice.isVisible() == True


def test_empty_key_value_displays_entire_catalog(
    qtbot: QtBot, tiled_client: BaseClient
):
    """Empty search fields should display normal catalog."""
    ...


def test_key_value_search(tiled_client: BaseClient):
    """Check key/value search displays correct rows."""
    # populate key and value textboxes
    input_key = "apple"
    input_value = "red"

    # perform search somehow
    ...

    # Check correct rows are displayed
    expected_search_results = ["a"]
    results = tiled_client.search(Key(input_key) == input_value)
    assert expected_search_results == list(results)


def test_key_regex_value_search(tiled_client: BaseClient):
    """Check key/RegEx value search displays correct rows."""
    # populate key and value (use regex) textboxes
    use_regex = True
    input_key = "animal"
    input_value = ".t"
    expected_search_results = ["c", "d", "e", "f", "structured_data"]
    results = tiled_client.search(Regex(input_key, input_value))
    assert expected_search_results == list(results)


def test_full_text_search(tiled_client: BaseClient):
    """Check FullText search displays correct rows."""
    # populate value textbox
    use_fulltext = True
    input_value = "cat"
    expected_search_results = ["c", "e", "f", "structured_data"]
    results = tiled_client.search(FullText(input_value))
    assert expected_search_results == list(results)
