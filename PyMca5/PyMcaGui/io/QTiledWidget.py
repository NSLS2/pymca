from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSplitter, QStyle, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget,
)
from PyQt5.QtCore import Qt

from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.io.TiledCatalogSelector import TiledCatalogSelector
from PyMca5.PyMcaGui.io.QTiledCatalogSelectorDialog import QTiledCatalogSelectorDialog


class QTiledWidget(QWidget):
    # To be displayed in Tiled Tab
    sigAddSelection = qt.pyqtSignal(object)
    sigRemoveSelection = qt.pyqtSignal(object)
    sigReplaceSelection = qt.pyqtSignal(object)
    sigOtherSignals = qt.pyqtSignal(object)

    def __init__(self, model=None):
        super().__init__()
        if model is None:
            self.model = TiledCatalogSelector()
        else:
            self.model = model
        self.dialog = QTiledCatalogSelectorDialog(model=self.model)

        self.data = None

        self.select_tiled_catalog = QPushButton("Select Tiled Catalog")
        layout = QVBoxLayout()
        layout.addWidget(self.select_tiled_catalog)
        layout.addStretch()
        self.setLayout(layout)

        self.select_tiled_catalog.clicked.connect(self.show_dialog)

        # if not data source exists, show only select tiled catalog button
        # else show normal widget

    def show_dialog(self):
        self.dialog.setWindowModality(Qt.ApplicationModal)
        self.dialog.exec_()
