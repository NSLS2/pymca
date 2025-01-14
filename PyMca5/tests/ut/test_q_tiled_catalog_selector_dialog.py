import enable_pymca_import  # noqa: F401

from itertools import cycle
from unittest.mock import patch

from PyQt5.QtWidgets import QLabel
from pytestqt.qtbot import QtBot
from tiled.client.base import BaseClient

from PyMca5.PyMcaGui.io.TiledCatalogSelector import TiledCatalogSelector
from PyMca5.PyMcaGui.io.QTiledCatalogSelectorDialog import (
    QTiledCatalogSelectorDialog, ClickableIndexedQLabel
)


def test_init(qtbot: QtBot, dialog_model: TiledCatalogSelector):
    """Can create a QTiledCatalogSelectorDialog object."""
    QTiledCatalogSelectorDialog(model=dialog_model)


def test_render(qtbot: QtBot, dialog_model: TiledCatalogSelector):
    """Can render a QTiledCatalogSelectorDialog window."""
    dialog = QTiledCatalogSelectorDialog(model=dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

# Functional tests...

def test_connection(
    qtbot: QtBot,
    dialog_model: TiledCatalogSelector,
    tiled_client: BaseClient,
):
    """Verify changes enacted by initiating a connection."""
    model = dialog_model
    expected_url = "http://local-tiled-app/api/v1/metadata/"

    model.url = expected_url
    dialog = QTiledCatalogSelectorDialog(model=model)
    dialog.show()
    qtbot.addWidget(dialog)

    with patch.object(model, "client_from_url") as mock_client_constructor:
        mock_client_constructor.return_value = tiled_client
        dialog.connect_button.click()
    
    assert expected_url in dialog.connection_label.text()


def test_url_editing(qtbot: QtBot, dialog_model: TiledCatalogSelector):
    """Verify changes enacted by interacting with the url_entry widget."""
    dialog = QTiledCatalogSelectorDialog(model=dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    # Default text shown
    assert dialog.url_entry.placeholderText() == "Enter a url"

    # Disply the URL when it is initialized in the model
    dialog_model.url = "Initial url"
    dialog_model.url_changed.emit()
    assert dialog.url_entry.displayText() == "Initial url"

    # Simulate editing the url_entry text
    dialog.url_entry.textEdited.emit("New url")
    dialog.url_entry.editingFinished.emit()
    assert dialog.model.url == "New url"

def test_url_set_through_model(
    qtbot: QtBot,
    dialog_model: TiledCatalogSelector,
    tiled_client: BaseClient,
):
    """Connects to a url that is set on the model after dialog creation."""
    dialog = QTiledCatalogSelectorDialog(model=dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    expected_url = "http://local-tiled-app/api/v1/metadata/"
    dialog.model.url = expected_url

    with patch.object(dialog_model, "client_from_url") as mock_client_constructor:
        mock_client_constructor.return_value = tiled_client
        dialog.connect_button.click()

    assert expected_url in dialog.connection_label.text()


def test_correct_rows_displayed(
    qtbot: QtBot,
    tiled_client_dialog_model: TiledCatalogSelector,
):
    """Check correct number of rows and contents are displyed."""
    dialog = QTiledCatalogSelectorDialog(model=tiled_client_dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    dialog.model.reset_client_view()

    assert dialog.catalog_table.rowCount() == 5

    expected_text = ["a", "b", "c", "d", "e"]

    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text


def test_navigation(
    qtbot: QtBot,
    tiled_client_dialog_model: TiledCatalogSelector,
):
    """Check table page contents when going to first/next/previous/last pages."""
    dialog = QTiledCatalogSelectorDialog(model=tiled_client_dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    dialog.model.reset_client_view()

    assert dialog.rows_per_page_selector.currentText() == "5"

    dialog.model.on_next_page_clicked()

    # Check last values show in new page
    expected_text = ["f", "structured_data"]

    assert len(expected_text) == dialog.catalog_table.rowCount()

    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text

    dialog.model.on_prev_page_clicked()

    expected_text = ["a", "b", "c", "d", "e"]

    assert len(expected_text) == dialog.catalog_table.rowCount()

    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text

    # Check last values show in last page
    dialog.model.on_last_page_clicked()

    expected_text = ["f", "structured_data"]

    assert len(expected_text) == dialog.catalog_table.rowCount()

    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text

    # Check first values show in first page
    dialog.model.on_first_page_clicked()

    expected_text = ["a", "b", "c", "d", "e"]

    assert len(expected_text) == dialog.catalog_table.rowCount()

    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text


def test_current_page_layout(
    qtbot: QtBot,
    tiled_client_dialog_model: TiledCatalogSelector,
):
    """Check current page layout of breadcrumbs updates correctly."""
    dialog = QTiledCatalogSelectorDialog(model=tiled_client_dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    dialog.model.enter_node("structured_data")
    expected_widget_text_order = ["root", " / ", "struc...", " / "]
    expected_widget_types = [ClickableIndexedQLabel, QLabel]

    for index, expected_widget_type, expected_widget_text in zip(
        range(dialog.current_path_layout.count()),
        cycle(expected_widget_types),
        expected_widget_text_order
    ):
        widget = dialog.current_path_layout.itemAt(index).widget()
        assert isinstance(widget, expected_widget_type)
        assert widget.text() == expected_widget_text

    dialog.model.exit_node()
    expected_widget_text_order = ["root", " / "]
    expected_widget_types = [ClickableIndexedQLabel, QLabel]

    for index, expected_widget_type, expected_widget_text in zip(
        range(dialog.current_path_layout.count()),
        cycle(expected_widget_types),
        expected_widget_text_order
    ):
        widget = dialog.current_path_layout.itemAt(index).widget()
        assert isinstance(widget, expected_widget_type)
        assert widget.text() == expected_widget_text

    dialog.model.enter_node("structured_data")

    dialog.model.jump_to_node(0)
    expected_widget_text_order = ["root", " / "]
    expected_widget_types = [ClickableIndexedQLabel, QLabel]

    for index, expected_widget_type, expected_widget_text in zip(
        range(dialog.current_path_layout.count()),
        cycle(expected_widget_types),
        expected_widget_text_order
    ):
        widget = dialog.current_path_layout.itemAt(index).widget()
        assert isinstance(widget, expected_widget_type)
        assert widget.text() == expected_widget_text


def test_clicking_breadcrumbs(
    qtbot: QtBot,
    tiled_client_dialog_model: TiledCatalogSelector,
):
    """Check clicking breadcrumbs displays correct contents."""
    dialog = QTiledCatalogSelectorDialog(model=tiled_client_dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    dialog.model.enter_node("structured_data")

    # Click "struc..." breadcrumb
    bc_widget = dialog.findChild(ClickableIndexedQLabel, 'structured_data')
    bc_widget.click()
    expected_text = ["..", "pets"]
    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text

    # Click root breadcrumb
    bc_widget = dialog.findChild(ClickableIndexedQLabel, 'root')
    bc_widget.click()
    expected_text = ["a", "b", "c", "d", "e"]
    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text


def test_current_location_label(
    qtbot: QtBot,
    tiled_client_dialog_model: TiledCatalogSelector,
):
    """Check the current location is properly displayed."""
    dialog = QTiledCatalogSelectorDialog(model=tiled_client_dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    assert dialog.rows_per_page_selector.currentText() == "5"
    assert f"of {len(dialog.model.client)}" in dialog.current_location_label.text()
    
    assert "1-5" in dialog.current_location_label.text()

    # Go to last page
    dialog.model.on_last_page_clicked()
    assert f"6-{len(dialog.model.client)}" in dialog.current_location_label.text()

    # Go to first page
    dialog.model.on_first_page_clicked()
    assert "1-5" in dialog.current_location_label.text()

def test_rows_per_page_selector_changed_updates_table(
    qtbot: QtBot,
    tiled_client_dialog_model: TiledCatalogSelector,
):
    """Check the table is updated when the rows per page is changed."""
    dialog = QTiledCatalogSelectorDialog(model=tiled_client_dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    assert dialog.rows_per_page_selector.currentText() == "5"
    assert dialog.catalog_table.rowCount() == 5

    # Change to 10 rows per page (index 1)
    dialog.rows_per_page_selector.setCurrentIndex(1)
    assert dialog.rows_per_page_selector.currentText() == "10"
    assert dialog.catalog_table.rowCount() == len(dialog.model.client)

    # Change back to 5 rows per page (index 0)
    dialog.rows_per_page_selector.setCurrentIndex(0)
    assert dialog.rows_per_page_selector.currentText() == "5"
    assert dialog.catalog_table.rowCount() == 5
