import logging
from collections import defaultdict
from typing import Callable, Mapping, Optional, Tuple

from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSplitter, QStyle, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget,
)
# TODO: test pyqtSignal vs Signal
from qtpy.QtCore import Qt, Signal
from tiled.structures.core import StructureFamily

from .TiledCatalogSelector import TiledCatalogSelector


_logger = logging.getLogger(__name__)


class PassThroughEventFilter(QObject):
    """React to desired events then pass each event to the parent filter."""
    def __init__(
        self,
        handlers: Mapping[QEvent.Type, Callable[[QEvent], None]],
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.handle_event = defaultdict(self.do_nothing_factory)
        self.handle_event.update(handlers)
    
    @staticmethod
    def do_nothing_factory():
        """Return a function that swallows its arguments and does nothing."""
        def do_nothing(*args, **kwargs):
            pass

        return do_nothing

    def eventFilter(
        self,
        obj: Optional[QObject],
        event: Optional[QEvent],
    ) -> bool:
        """Respond to the event and then pass it to the parent filter."""
        self.handle_event[event.type()](event)

        return super().eventFilter(obj, event)


class QTiledCatalogSelectorDialog(QDialog):
    """A dialog window to find and select a Tiled CatalogOfBlueskyRuns."""
    def __init__(
        self,
        model: TiledCatalogSelector,
        parent: Optional[QWidget] = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize..."""
        _logger.debug("QTiledCatalogSelectorDialog.__init__()...")

        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.create_layout()
        self.connect_model_signals()
        self.connect_model_slots()
        self.initialize_values()

    def create_layout(self) -> None:
        """Create the visual layout of widgets for the dialog."""
        _logger.debug("QTiledCatalogSelectorDialog.create_layout()...")

        # Connection elements
        self.url_entry = QLineEdit()
        self.connect_button = QPushButton("Connect")
        self.connection_label = QLabel("No url connected")
        self.connection_widget = QWidget()

        # Connection layout
        connection_layout = QVBoxLayout()
        connection_layout.addWidget(self.url_entry)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.connection_label)
        connection_layout.addStretch()
        self.connection_widget.setLayout(connection_layout)

        # Navigation elements
        self.rows_per_page_label = QLabel("Rows per page: ")
        self.rows_per_page_selector = QComboBox()

        self.current_location_label = QLabel()
        self.previous_page = ClickableQLabel("<")
        self.next_page = ClickableQLabel(">")
        self.navigation_widget = QWidget()

        # Navigation layout
        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.rows_per_page_label)
        navigation_layout.addWidget(self.rows_per_page_selector)
        navigation_layout.addWidget(self.current_location_label)
        navigation_layout.addWidget(self.previous_page)
        navigation_layout.addWidget(self.next_page)
        self.navigation_widget.setLayout(navigation_layout)

        # Current path layout
        self.current_path_label = QLabel()
        # self._rebuild_current_path_label()

        # Catalog table elements
        self.catalog_table = QTableWidget(0, 1)
        self.catalog_table.horizontalHeader().setStretchLastSection(True)
        self.catalog_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )  # disable editing
        self.catalog_table.horizontalHeader().hide()  # remove header
        self.catalog_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )  # disable multi-select
        # self.catalog_table.itemDoubleClicked.connect(
        #     self._on_item_double_click
        # )
        # self.catalog_table.itemSelectionChanged.connect(self._on_item_selected)
        self.catalog_table_widget = QWidget()
        self.catalog_breadcrumbs = None

        # Info layout
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.load_button = QPushButton("Open")
        self.load_button.setEnabled(False)
        # self.load_button.clicked.connect(self._on_load)
        catalog_info_layout = QHBoxLayout()
        catalog_info_layout.addWidget(self.catalog_table)
        load_layout = QVBoxLayout()
        load_layout.addWidget(self.info_box)
        load_layout.addWidget(self.load_button)
        catalog_info_layout.addLayout(load_layout)

        # Catalog table layout
        catalog_table_layout = QVBoxLayout()
        catalog_table_layout.addWidget(self.current_path_label)
        catalog_table_layout.addLayout(catalog_info_layout)
        catalog_table_layout.addWidget(self.navigation_widget)
        catalog_table_layout.addStretch(1)
        self.catalog_table_widget.setLayout(catalog_table_layout)
        self.catalog_table_widget.setVisible(False)

        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Orientation.Vertical)

        self.splitter.addWidget(self.connection_widget)
        self.splitter.addWidget(self.catalog_table_widget)

        self.splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

    def initialize_values(self) -> None:
        """Initialize widget values."""
        self.reset_url_entry()
        self.reset_rows_per_page()

    def reset_url_entry(self) -> None:
        """Reset the state of the url_entry widget."""
        _logger.debug("QTiledCatalogSelectorDialog.reset_url_entry()...")

        if not self.model.url:
            self.url_entry.setPlaceholderText("Enter a url")
        else:
            self.url_entry.setText(self.model.url)

    def reset_rows_per_page(self) -> None:
        """Reset the state of the rows_per_page_selector widget."""
        _logger.debug("QTiledCatalogSelectorDialog.reset_rows_per_page()...")

        # TODO: Should probably make these a property (of the model?)
        self.rows_per_page_selector.addItems(["5", "10", "25"])
        self.rows_per_page_selector.setCurrentIndex(0)
        self._rows_per_page = int(
            self.rows_per_page_selector.currentText()
        )

    def populate_table(self):
        original_state = {}
        # TODO: may need if condition if we implement a disconnect button
        self.catalog_table_widget.setVisible(True)

        original_state["blockSignals"] = self.catalog_table.blockSignals(True)
        # Remove all rows first
        while self.catalog_table.rowCount() > 0:
            self.catalog_table.removeRow(0)

        if self.model.node_path_parts:
            # add breadcrumbs
            self.catalog_breadcrumbs = QTableWidgetItem("..")
            self.catalog_table.insertRow(0)
            self.catalog_table.setItem(0, 0, self.catalog_breadcrumbs)

        # Then add new rows
        for row in range(self._rows_per_page):
            last_row_position = self.catalog_table.rowCount()
            self.catalog_table.insertRow(last_row_position)
        node_offset = self._rows_per_page * self.model._current_page
        # Fetch a page of keys.
        items = self.model.get_current_node().items()[
            node_offset : node_offset + self._rows_per_page
        ]
        # Loop over rows, filling in keys until we run out of keys.
        start = 1 if self.model.node_path_parts else 0
        for row_index, (key, value) in zip(
            range(start, self.catalog_table.rowCount()), items
        ):
            family = value.item["attributes"]["structure_family"]

            if family == StructureFamily.container:
                icon = self.style().standardIcon(QStyle.SP_DirHomeIcon)
            elif family == StructureFamily.array:
                icon = self.style().standardIcon(
                    QStyle.SP_FileIcon
                )
            else:
                icon = self.style().standardIcon(
                    QStyle.SP_TitleBarContextHelpButton
                )

            self.catalog_table.setItem(
                row_index, 0, QTableWidgetItem(icon, key)
            )

        # remove extra rows
        for _ in range(self._rows_per_page - len(items)):
            self.catalog_table.removeRow(self.catalog_table.rowCount() - 1)

        headers = [
            str(x + 1)
            for x in range(
                node_offset, node_offset + self.catalog_table.rowCount()
            )
        ]
        if self.model.node_path_parts:
            headers = [""] + headers

        self.catalog_table.setVerticalHeaderLabels(headers)
        self._clear_metadata()
        self.catalog_table.blockSignals(original_state["blockSignals"])

    def _clear_metadata(self):
        self.info_box.setText("")
        self.load_button.setEnabled(False)

    def connect_model_signals(self) -> None:
        """Connect dialog slots to model signals."""
        _logger.debug("QTiledCatalogSelectorDialog.connect_model_signals()...")

        @self.model.client_connected.connect
        def on_client_connected(url: str, api_url: str):
            self.connection_label.setText(f"Connected to {url}")
            # TODO: Display the contents of the Tiled node
            ...

        @self.model.client_connection_error.connect
        def on_client_connection_error(error_msg: str):
            # TODO: Display the error message; suggest a remedy
            ...

        @self.model.table_changed.connect
        def on_table_changed(node_path_parts: Tuple[str]):
            _logger.debug(f"on_table_changed(): {node_path_parts = }")
            self.populate_table()

        @self.model.url_validation_error.connect
        def on_url_validation_error(error_msg: str):
            # TODO: Display the error message; visual emphasis of url_entry
            ...

        self.model.url_changed.connect(self.reset_url_entry)

    def connect_model_slots(self) -> None:
        """Connect model slots to dialog signals."""
        _logger.debug("QTiledCatalogSelectorDialog.connect_model_slots()...")

        model = self.model

        self.url_entry.textEdited.connect(model.on_url_text_edited)
        self.url_entry.editingFinished.connect(model.on_url_editing_finished)
        self.connect_button.clicked.connect(model.on_connect_clicked)


class ClickableQLabel(QLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        self.clicked.emit()


if __name__ == '__main__':
    from sys import argv
    from PyQt5.QtWidgets import QApplication, QMainWindow

    app = QApplication(argv)
    window = QMainWindow()
    model = TiledCatalogSelector(parent=app)
    model.url = "https://tiled-demo.blueskyproject.io/api"
    dialog = QTiledCatalogSelectorDialog(model=model)

    window.show()
    window.setCentralWidget(dialog)
    # breakpoint()
    exit(app.exec_())
