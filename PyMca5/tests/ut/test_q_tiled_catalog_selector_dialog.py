import enable_pymca_import  # noqa: F401

from unittest.mock import patch

from pytestqt.qtbot import QtBot
from tiled.client.base import BaseClient


from PyMca5.PyMcaGui.io.TiledCatalogSelector import TiledCatalogSelector
from PyMca5.PyMcaGui.io.QTiledCatalogSelectorDialog import QTiledCatalogSelectorDialog


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
    """Check table page contents when going to next/previous pages."""
    dialog = QTiledCatalogSelectorDialog(model=tiled_client_dialog_model)
    dialog.show()
    qtbot.addWidget(dialog)

    dialog.model.reset_client_view()

    assert dialog.rows_per_page_selector.currentText() == "5"

    dialog.model.on_next_page_clicked()

    # Check last value shows in new page
    expected_text = ["f"]

    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text

    dialog.model.on_prev_page_clicked()

    expected_text = ["a", "b", "c", "d", "e"]

    for row_num, text in enumerate(expected_text):
        assert dialog.catalog_table.item(row_num, 0).text() == text
