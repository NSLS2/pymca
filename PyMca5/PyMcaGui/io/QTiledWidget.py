import logging
from typing import Callable, Mapping, Optional, Tuple

from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSplitter, QStyle, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget,
)
from PyQt5.QtCore import Qt
from tiled.structures.core import StructureFamily

from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.io.TiledCatalogSelector import TiledCatalogSelector
from PyMca5.PyMcaGui.io.TiledDataChannelTable import QTiledDataChannelTable
from PyMca5.PyMcaGui.io.TiledRunSelector import TiledRunSelector
from PyMca5.PyMcaGui.io.QTiledCatalogSelectorDialog import (
    QTiledCatalogSelectorDialog, ClickableQLabel, ClickableIndexedQLabel
)


_logger = logging.getLogger(__name__)


class QTiledWidget(QWidget):
    # To be displayed in Tiled Tab
    sigAddSelection = qt.pyqtSignal(object)
    sigRemoveSelection = qt.pyqtSignal(object)
    sigReplaceSelection = qt.pyqtSignal(object)
    sigOtherSignals = qt.pyqtSignal(object)

    def __init__(self, model=None, dialog_model=None):
        super().__init__()
        if dialog_model is None:
            dialog_model = TiledCatalogSelector()
        self.dialog = QTiledCatalogSelectorDialog(model=dialog_model)

        if model is None:
            self.model = TiledRunSelector()
        else:
            self.model = model

        self.data = None

        self.create_layout()
        self.connect_model_signals()
        self.connect_model_slots()
        self.connect_self_signals()
        self.initialize_values()

    def create_layout(self):
        self.select_tiled_catalog = QPushButton("Select Tiled Catalog")

        # if not data source exists, show only select tiled catalog button
        # else show normal widget

        self.connection_label = QLabel("No url connected")

        # Navigation elements
        self.rows_per_page_label = QLabel("Rows per page: ")
        self.rows_per_page_selector = QComboBox()

        self.current_location_label = QLabel()
        self.first_page = ClickableQLabel("<<")
        self.previous_page = ClickableQLabel("<")
        self.next_page = ClickableQLabel(">")
        self.last_page = ClickableQLabel(">>")
        self.navigation_widget = QWidget()

        # Navigation layout
        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.rows_per_page_label)
        navigation_layout.addWidget(self.rows_per_page_selector)
        navigation_layout.addWidget(self.current_location_label)
        navigation_layout.addWidget(self.first_page)
        navigation_layout.addWidget(self.previous_page)
        navigation_layout.addWidget(self.next_page)
        navigation_layout.addWidget(self.last_page)
        self.navigation_widget.setLayout(navigation_layout)

        # Current path layout
        self.current_path_widget = QWidget()
        self.current_path_layout = QHBoxLayout()
        self.current_path_layout.setAlignment(Qt.AlignLeft)
        self.current_path_widget.setLayout(self.current_path_layout)
        self._rebuild_current_path_layout()

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
        self.catalog_table_widget = QWidget()
        self.catalog_breadcrumbs = None

        # Info layout
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.open_button = QPushButton("Open")
        self.open_button.setEnabled(False)
        catalog_info_layout = QHBoxLayout()
        catalog_info_layout.addWidget(self.catalog_table)
        load_layout = QVBoxLayout()
        load_layout.addWidget(self.info_box)
        load_layout.addWidget(self.open_button)
        catalog_info_layout.addLayout(load_layout)

        # Catalog table layout
        catalog_table_layout = QVBoxLayout()
        catalog_table_layout.addWidget(self.current_path_widget)
        catalog_table_layout.addLayout(catalog_info_layout)
        catalog_table_layout.addWidget(self.navigation_widget)
        catalog_table_layout.addStretch(1)
        self.catalog_table_widget.setLayout(catalog_table_layout)
        self.catalog_table_widget.setVisible(False)

        # Data Channels Table
        self.data_channels_table = QTiledDataChannelTable()
        self.data_channels_table.setVisible(False)

        # Command Button Elements
        self.command_button_widget = QWidget()
        self.command_button_widget.setSizePolicy(qt.QSizePolicy.Minimum,
                                   qt.QSizePolicy.Minimum)
        add_button = qt.QPushButton("ADD", self.command_button_widget)
        remove_button = qt.QPushButton("REMOVE", self.command_button_widget)
        replace_button = qt.QPushButton("REPLACE", self.command_button_widget)

        # Command Buttons Layout
        command_button_layout = qt.QHBoxLayout(self.command_button_widget)
        command_button_layout.addWidget(add_button)
        command_button_layout.addWidget(remove_button)
        command_button_layout.addWidget(replace_button)
        command_button_layout.setContentsMargins(5, 5, 5, 5)
        self.command_button_widget.setVisible(False)

        data_channel_layout = QVBoxLayout()
        data_channel_layout.addWidget(self.data_channels_table)
        data_channel_layout.addWidget(self.command_button_widget)
        
        self.data_channel_widget = QWidget()
        self.data_channel_widget.setLayout(data_channel_layout)

        self.splitter = QSplitter(self)
        self.splitter.setOrientation(Qt.Orientation.Vertical)

        self.splitter.addWidget(self.connection_label)
        self.splitter.addWidget(self.catalog_table_widget)
        self.splitter.addWidget(self.data_channel_widget)

        self.splitter.setStretchFactor(2, 2)

        layout = QVBoxLayout()
        layout.addWidget(self.select_tiled_catalog)
        layout.addWidget(self.connection_label)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

    def initialize_values(self) -> None:
        """Initialize widget values."""
        self.reset_rows_per_page()

    def _rebuild_current_path_layout(self):
        """Reset the clickable widgets for the current path breadcrumbs."""
        bc_widget = ClickableIndexedQLabel("root", index=0)
        bc_widget.setObjectName("root")
        bc_widget.clicked.connect(self._on_breadcrumb_clicked)
        breadcrumbs = [bc_widget]

        for i, node_id in enumerate(self.model.node_path_parts, start=1):
            if len(node_id) > self.NODE_ID_MAXLEN:
                short_node_id = node_id[: self.NODE_ID_MAXLEN - 3] + "..."
                bc_widget = ClickableIndexedQLabel(short_node_id, index=i)
            else:
                bc_widget = ClickableIndexedQLabel(node_id, index=i)
            
            bc_widget.setObjectName(node_id)
            bc_widget.clicked.connect(self._on_breadcrumb_clicked)
            breadcrumbs.append(bc_widget)
        
        # remove all widgets from current_path_layout
        self.remove_current_path_layout_widgets()

        for breadcrumb in breadcrumbs:
            self.current_path_layout.addWidget(breadcrumb)
            self.current_path_layout.addWidget(QLabel(" / "))

    def remove_current_path_layout_widgets(self):
        """Remove unneeded path widgets and free the memory."""
        for index in reversed(range(self.current_path_layout.count())):
            widget = self.current_path_layout.itemAt(index).widget()
            self.current_path_layout.removeWidget(widget)
            widget.deleteLater()

    def reset_rows_per_page(self) -> None:
        """Reset the state of the rows_per_page_selector widget."""
        _logger.debug("QTiledCatalogSelectorDialog.reset_rows_per_page()...")

        self.rows_per_page_selector.addItems(
            [str(option) for option in self.model._rows_per_page_options]
        )
        self.rows_per_page_selector.setCurrentIndex(self.model._rows_per_page_index)

    def _set_current_location_label(self):
        starting_index = self.model._current_page * self.model.rows_per_page + 1
        ending_index = min(
            self.model.rows_per_page * (self.model._current_page + 1),
            len(self.model.get_current_node()),
        )
        current_location_text = f"{starting_index}-{ending_index} of {len(self.model.get_current_node())}"
        self.current_location_label.setText(current_location_text)

    def populate_run_table(self):
        original_state = {}
        # TODO: may need if condition if we implement a disconnect button
        self.catalog_table_widget.setVisible(True)
        self.data_channels_table.setVisible(True)
        self.data_channels_table.format_table()
        self.command_button_widget.setVisible(True)

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
        rows_per_page = self.model.rows_per_page
        for _ in range(rows_per_page):
            last_row_position = self.catalog_table.rowCount()
            self.catalog_table.insertRow(last_row_position)
        node_offset = rows_per_page * self.model._current_page
        # Fetch a page of keys.
        items = self.model.get_current_node().items()[
            node_offset : node_offset + rows_per_page
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
        for _ in range(rows_per_page - len(items)):
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

    # def populate_data_channel_table(self):
    #     original_state = {}

    #     original_state["blockSignals"] = self.catalog_table.blockSignals(True)
    #     # Remove all rows first
    #     while self.catalog_table.rowCount() > 0:
    #         self.catalog_table.removeRow(0)

    #     if self.model.node_path_parts:
    #         # add breadcrumbs
    #         self.catalog_breadcrumbs = QTableWidgetItem("..")
    #         self.catalog_table.insertRow(0)
    #         self.catalog_table.setItem(0, 0, self.catalog_breadcrumbs)

    #     # Then add new rows
    #     rows_per_page = self.model.rows_per_page
    #     for _ in range(rows_per_page):
    #         last_row_position = self.catalog_table.rowCount()
    #         self.catalog_table.insertRow(last_row_position)
    #     node_offset = rows_per_page * self.model._current_page
    #     # Fetch a page of keys.
    #     items = self.model.get_current_node().items()[
    #         node_offset : node_offset + rows_per_page
    #     ]
    #     # Loop over rows, filling in keys until we run out of keys.
    #     start = 1 if self.model.node_path_parts else 0
    #     for row_index, (key, value) in zip(
    #         range(start, self.catalog_table.rowCount()), items
    #     ):
    #         family = value.item["attributes"]["structure_family"]

    #         if family == StructureFamily.container:
    #             icon = self.style().standardIcon(QStyle.SP_DirHomeIcon)
    #         elif family == StructureFamily.array:
    #             icon = self.style().standardIcon(
    #                 QStyle.SP_FileIcon
    #             )
    #         else:
    #             icon = self.style().standardIcon(
    #                 QStyle.SP_TitleBarContextHelpButton
    #             )

    #         self.catalog_table.setItem(
    #             row_index, 0, QTableWidgetItem(icon, key)
    #         )

    #     # remove extra rows
    #     for _ in range(rows_per_page - len(items)):
    #         self.catalog_table.removeRow(self.catalog_table.rowCount() - 1)

    #     headers = [
    #         str(x + 1)
    #         for x in range(
    #             node_offset, node_offset + self.catalog_table.rowCount()
    #         )
    #     ]
    #     if self.model.node_path_parts:
    #         headers = [""] + headers

    #     self.catalog_table.setVerticalHeaderLabels(headers)
    #     self._clear_metadata()
    #     self.catalog_table.blockSignals(original_state["blockSignals"])

    def populate_data_channel_table(self, child_node):
        # For now, always select data from the primary stream
        channel_list = self.model.client[child_node]["primary", "data"].keys()
        
        self.data_channels_table.clear_table()
        self.data_channels_table.build_table(channel_list)

    def _clear_metadata(self):
        self.info_box.setText("")
        self.open_button.setEnabled(False)

    def _on_item_selected(self):
        model = self.model

        selected = self.catalog_table.selectedItems()
        if not selected or (item := selected[0]) is self.catalog_breadcrumbs:
            self._clear_metadata()
            return

        child_node_path = item.text()
        model.on_item_selected(child_node_path)

        self.info_box.setText(model.info_text)
        self.open_button.setEnabled(model.open_button_enabled)

    def _on_item_double_click(self, item):
        if item is self.catalog_breadcrumbs:
            self.model.exit_node()
            return
        self.model.open_node(item.text())
        self.open_button.setEnabled(False)

    def _on_load(self):
        selected = self.catalog_table.selectedItems()
        if not selected:
            return
        item = selected[0]
        self.model.open_run(item.text())
        self.populate_data_channel_table(item.text())

    def _on_breadcrumb_clicked(self, node_index):
        self.model.jump_to_node(node_index)

    def show_dialog(self):
        self.dialog.setWindowModality(Qt.ApplicationModal)
        self.dialog.exec_()

        # TODO: Maybe can pass in rows_per_page related args from dialog?
        # i.e. User sets rows_per_page to 10 in catalog selector and that gets
        # passed into the run selector

        self.model.url = self.dialog.model.client[*self.dialog.model.selected_catalog_path].uri

        print(f"{self.model.url = }")

        # print(f"{self.dialog.model.selected_catalog_path}")
        # print(f"{self.dialog.model.client[*self.dialog.model.selected_catalog_path].uri}")

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
            if self.model.client is None:
                # TODO: handle disconnecting from tiled client later
                return
            self.populate_run_table()
            self._rebuild_current_path_layout()
            self._set_current_location_label()

        self.model.url_changed.connect(self.model.on_url_changed)

    def connect_model_slots(self) -> None:
        """Connect model slots to dialog signals."""
        _logger.debug("QTiledCatalogSelectorDialog.connect_model_slots()...")

        model = self.model

        self.first_page.clicked.connect(model.on_first_page_clicked)
        self.next_page.clicked.connect(model.on_next_page_clicked)
        self.previous_page.clicked.connect(model.on_prev_page_clicked)
        self.last_page.clicked.connect(model.on_last_page_clicked)
        self.rows_per_page_selector.currentIndexChanged.connect(self.model.on_rows_per_page_changed)

    def connect_self_signals(self):
        # TODO find another way to do this?
        self.select_tiled_catalog.clicked.connect(self.show_dialog)
        self.catalog_table.itemSelectionChanged.connect(self._on_item_selected)
        self.catalog_table.itemDoubleClicked.connect(
            self._on_item_double_click
        )
        self.open_button.clicked.connect(self._on_load)


# # Command Buttons Connections
# addButton.clicked.connect(self._addClicked)
# replaceButton.clicked.connect(self._replaceClicked)
# removeButton.clicked.connect(self._removeClicked)