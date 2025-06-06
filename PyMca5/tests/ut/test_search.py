import pytest

from typing import List
from unittest.mock import Mock, patch

from pytestqt.qtbot import QtBot
from tiled.client.base import BaseClient
from tiled.queries import FullText, Key, Regex

from PyMca5.PyMcaGui.io.QTiledSearch import QTiledSearchWidget
from PyMca5.PyMcaGui.io.QTiledWidget import QTiledWidget
from PyMca5.PyMcaGui.io.TiledRunSelector import TiledRunSelector


def test_init(qtbot: QtBot, tiled_client_run_selector_model: TiledRunSelector):
    """Can create a QTiledSearchWidget object."""
    QTiledSearchWidget(model=tiled_client_run_selector_model)


def test_render(qtbot: QtBot, tiled_client_run_selector_model: TiledRunSelector):
    """Can render a QTiledSearchWidget window."""
    search = QTiledSearchWidget(model=tiled_client_run_selector_model)
    search.show()
    qtbot.addWidget(search)


def test_fulltext_checkbox_disables_key_field(qtbot: QtBot):
    """Checked FullText checkbox should disable key and RegEx elements."""
    search = QTiledSearchWidget(model=None)
    search.show()
    qtbot.addWidget(search)
    # Key label/entry and regex checkbox should start enabled
    assert all(
        [
            element.isEnabled()
            for element in [
                search.key_label,
                search.key_entry,
                search.regex_checkbox,
            ]
        ]
    )
    # full text hint should start invisible
    assert search.full_text_hint.isVisible() == False

    search.full_text_checkbox.click()

    # Key label/entry and regex checkbox should be disabled now
    assert not all(
        [
            element.isEnabled()
            for element in [
                search.key_label,
                search.key_entry,
                search.regex_checkbox,
            ]
        ]
    )
    # full text hint should now be visible
    assert search.full_text_hint.isVisible() == True

    # Clicking the fulltext checkbox again should set everything back to normal
    search.full_text_checkbox.click()

    # Key label/entry and regex checkbox should be enabled again
    assert all(
        [
            element.isEnabled()
            for element in [
                search.key_label,
                search.key_entry,
                search.regex_checkbox,
            ]
        ]
    )
    # full text hint should be invisible again
    assert search.full_text_hint.isVisible() == False


def test_regex_checkbox_disables_fulltext_checkbox(qtbot: QtBot):
    """Checked RegEx checkbox should hide FullText checkbox."""
    search = QTiledSearchWidget(model=None)
    search.show()
    qtbot.addWidget(search)

    # on init
    assert search.full_text_checkbox.isEnabled() == True

    # on checking regex checkbox
    search.regex_checkbox.click()
    assert search.full_text_checkbox.isEnabled() == False

    # on unchecking regex checkbox
    search.regex_checkbox.click()
    assert search.full_text_checkbox.isEnabled() == True


@pytest.mark.parametrize(
    "key, value, fulltext_checked, regex_checked, search_type",
    (
        ("a", "a", False, False, "key_value"),
        ("", "", False, False, "no_search"),
        ("a", "", False, False, "no_search"),
        ("", "a", False, False, "no_search"),
        ("a", "a", False, True, "regex"),
        ("", "", False, True, "no_search"),
        ("a", "", False, True, "no_search"),
        ("", "a", False, True, "no_search"),
        ("", "a", True, False, "full_text"),
        ("", "", True, False, "no_search"),
        ("a", "", True, False, "no_search"),
    )
)
def test_search_types(
    key: str,
    value: str,
    fulltext_checked: bool,
    regex_checked: bool,
    search_type: str,
    qtbot: QtBot,
    tiled_client_run_selector_model: TiledRunSelector
):
    """Check correct search types are set."""
    search = QTiledSearchWidget(model=tiled_client_run_selector_model)
    search.show()
    qtbot.addWidget(search)

    search.key_entry.setText(key)
    search.value_entry.setText(value)
    search.full_text_checkbox.setChecked(fulltext_checked)
    search.regex_checkbox.setChecked(regex_checked)

    assert search._search() == search_type


@pytest.mark.xfail
def test_empty_search_results_displays_empty_table(
    qtbot: QtBot, tiled_client_run_selector_model: TiledRunSelector
):
    """Empty search results should display an empty table."""
    tiled_widget = QTiledWidget(model=tiled_client_run_selector_model)
    tiled_widget.show()
    qtbot.addWidget(tiled_widget)

    # FIXME: test data has no start doc, fails to initialize QTiledWidget
    ...


@pytest.mark.xfail
def test_invalid_search_displays_entire_catalog(
    qtbot: QtBot, tiled_client_run_selector_model: TiledRunSelector
):
    """Empty search fields should display normal catalog."""
    tiled_widget = QTiledWidget(model=tiled_client_run_selector_model)
    tiled_widget.show()
    qtbot.addWidget(tiled_widget)

    # FIXME: test data has no start doc, fails to initialize QTiledWidget
    ...


@pytest.mark.xfail
def test_valid_search_displays_search_results(
    qtbot: QtBot, tiled_client_run_selector_model: TiledRunSelector
):
    """Valid search should display search rows in table."""
    tiled_widget = QTiledWidget(model=tiled_client_run_selector_model)
    tiled_widget.show()
    qtbot.addWidget(tiled_widget)

    # FIXME: test data has no start doc, fails to initialize QTiledWidget
    ...


@pytest.mark.parametrize(
    "key, value, search_type, expected_results",
    (
        ("apple", "red", "key_value", ["a"]),
        ("apple", "something", "key_value", []),
        ("animal", ".t", "regex", ["c", "d", "e", "f", "structured_data"]),
        ("animal", "z", "regex", []),
        ("", "cat", "full_text", ["c", "e", "f", "structured_data"]),
        ("", "ca", "full_text", []),
    )
)
def test_run_selctor_model_search(
    key: str,
    value: str,
    search_type: str,
    expected_results: List[str],
    tiled_client: BaseClient
):
    """Check model search return correct data."""
    model = TiledRunSelector(client=tiled_client)
    results = model.search(key, value, search_type)

    assert list(results) == expected_results


def test_run_selector_search_results(tiled_client: BaseClient):
    """Check model search results updated correctly."""
    model = TiledRunSelector(client=tiled_client)
    # init search_results == None
    assert model.search_results == None

    with patch.object(model, "table_changed") as mock_signal:
        mock_signal.emit = Mock()

        # valid search, empty results, non-matching previous search_results
        # emits table_changed
        model.on_search("a", "a", search_type="key_value")
        assert list(model.search_results) == []
        assert mock_signal.emit.call_count == 1

        # valid search, empty results, matching previous search_results
        # does not emit table_changed
        mock_signal.emit.reset_mock()
        model.on_search("b", "b", search_type="key_value")
        assert list(model.search_results) == []
        assert mock_signal.emit.call_count == 0

        # valid search, non-empty results, non-matching previous search_results
        # emits table_changed
        mock_signal.emit.reset_mock()
        model.on_search("apple", "red", search_type="key_value")
        assert list(model.search_results) == ["a"]
        assert mock_signal.emit.call_count == 1

        # invalid search, non-matching previous search_results
        # emits table_changed
        mock_signal.emit.reset_mock()
        model.on_search("b", "b", search_type="no_search")
        assert model.search_results == None
        assert mock_signal.emit.call_count == 1
