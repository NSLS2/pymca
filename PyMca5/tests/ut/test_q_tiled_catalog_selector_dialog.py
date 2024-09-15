import enable_pymca_import  # noqa: F401

from pytestqt.qtbot import QtBot

from PyMca5.PyMcaGui.io.QTiledCatalogSelectorDialog import QTiledCatalogSelectorDialog


def test_init(qtbot: QtBot):
    """Can create a QTiledCatalogSelectorDialog object."""
    QTiledCatalogSelectorDialog()


def test_render(qtbot: QtBot):
    """Can render a QTiledCatalogSelectorDialog window."""
    dialog = QTiledCatalogSelectorDialog()
    dialog.show()
    qtbot.addWidget(dialog)
