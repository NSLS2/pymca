import logging
from typing import Callable, Mapping, Optional, Tuple

from datetime import datetime

from PyQt5.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSplitter, QStyle, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget, QHeaderView
)
from PyQt5.QtCore import Qt
from tiled.structures.core import StructureFamily

from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMcaGui.io.TiledCatalogSelector import TiledCatalogSelector
from PyMca5.PyMcaGui.io.QTiledDataChannelTable import QTiledDataChannelTable
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
        self.catalog_table = QTableWidget(0, 6)
        self.catalog_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.catalog_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.catalog_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.catalog_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )  # disable editing
        self.catalog_table.setHorizontalHeaderLabels(
            ["Scan ID", "UID", "Plan Name", "Start Time", "Stop Time", "Status"]
        )
        self.catalog_table.wordWrap = True
        self.catalog_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )  # disable multi-select
        self.catalog_table_widget = QWidget()
        self.catalog_breadcrumbs = None

        # Info layout
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.open_button = QPushButton("Import data")
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
        self.data_channel_table = QTiledDataChannelTable()
        self.data_channel_table.setVisible(False)

        # Command Button Elements
        self.command_button_widget = QWidget()
        self.command_button_widget.setSizePolicy(qt.QSizePolicy.Minimum,
                                   qt.QSizePolicy.Minimum)
        self.add_button = qt.QPushButton("ADD", self.command_button_widget)
        self.remove_button = qt.QPushButton("REMOVE", self.command_button_widget)
        self.replace_button = qt.QPushButton("REPLACE", self.command_button_widget)

        # Command Buttons Layout
        command_button_layout = qt.QHBoxLayout(self.command_button_widget)
        command_button_layout.addWidget(self.add_button)
        command_button_layout.addWidget(self.remove_button)
        command_button_layout.addWidget(self.replace_button)
        command_button_layout.setContentsMargins(5, 5, 5, 5)
        self.command_button_widget.setVisible(False)

        data_channel_layout = QVBoxLayout()
        data_channel_layout.addWidget(self.data_channel_table)
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
        _logger.debug("QTiledWidget.reset_rows_per_page()...")

        self.rows_per_page_selector.addItems(
            [str(option) for option in self.model._rows_per_page_options]
        )
        self.rows_per_page_selector.setCurrentIndex(self.model._rows_per_page_index)

    def _set_current_location_label(self):
        _logger.debug(f"                                      {len(self.model.get_current_node())}")
        starting_index = self.model._current_page * self.model.rows_per_page + 1
        ending_index = min(
            self.model.rows_per_page * (self.model._current_page + 1),
            len(self.model.get_current_node()),
        )
        current_location_text = f"{starting_index}-{ending_index} of {len(self.model.get_current_node())}"
        _logger.debug(f"         Before setText              {self.current_location_label.text()}")
        self.current_location_label.setText(current_location_text)
        _logger.debug(f"         After setText               {self.current_location_label.text()}")
        self.current_location_label.update()

    def populate_run_table(self):
        original_state = {}
        # TODO: may need if condition if we implement a disconnect button
        self.catalog_table_widget.setVisible(True)
        self.data_channel_table.setVisible(True)
        self.data_channel_table.format_table()
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
            start_doc = value.start
            scan_id = start_doc.get("scan_id")
            plan_name = start_doc.get("plan_name")
            start_time = start_doc.get("start_datetime")
            if start_time is None:
                start_time = datetime.fromtimestamp(start_doc.get("time")).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            else:
                start_time = datetime.fromisoformat(start_time).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            stop_doc = value.stop
            if stop_doc is None:
                stop_doc = {}
            exit_status = stop_doc.get("exit_status")
            if exit_status == "success":
                status_icon = self.style().standardIcon(QStyle.SP_DialogApplyButton)
            else:
                status_icon = self.style().standardIcon(QStyle.SP_DialogCancelButton)
            stop_time = stop_doc.get("time")
            if stop_time is None:
                stop_time = ""
            else:
                stop_time = datetime.fromtimestamp(stop_time).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

            family = value.item["attributes"]["structure_family"]

            if family == StructureFamily.container:
                # Change the icon for BlueskyRuns so it doesn't look like
                # users should click into the runs
                icon = self.style().standardIcon(QStyle.SP_FileIcon)
            elif family == StructureFamily.array:
                icon = self.style().standardIcon(
                    QStyle.SP_FileIcon
                )
            else:
                icon = self.style().standardIcon(
                    QStyle.SP_TitleBarContextHelpButton
                )

            # columns: ["Scan ID", "UID", "Plan Name", "Start Time", "Stop Time", "Status"]
            # scan_id
            self.catalog_table.setItem(
                row_index, 0, QTableWidgetItem(icon, str(scan_id))
            )
            # first 8 chars of uid
            self.catalog_table.setItem(
                row_index, 1, QTableWidgetItem(key[:8])
            )
            # plan_name
            self.catalog_table.setItem(
                row_index, 2, QTableWidgetItem(plan_name)
            )
            # start_time
            self.catalog_table.setItem(
                row_index, 3, QTableWidgetItem(str(start_time).replace(" ", "\n"))
            )
            # stop_time
            self.catalog_table.setItem(
                row_index, 4, QTableWidgetItem(str(stop_time))
            )
            # exit_status
            self.catalog_table.setItem(
                row_index, 5, QTableWidgetItem(status_icon, "")
            )
            self.catalog_table.resizeRowsToContents()

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

    def populate_data_channel_table(self, child_node):
        # For now, always select data from the primary stream
        channel_list = self.model.client[child_node]["primary", "data"].keys()
        
        self.data_channel_table.clear_table()
        self.data_channel_table.build_table(channel_list)

    def _clear_metadata(self):
        self.info_box.setText("")
        self.open_button.setEnabled(False)

    def _on_item_selected(self):
        model = self.model

        selected = self.catalog_table.selectedItems()
        if not selected or selected[0] is self.catalog_breadcrumbs:
            self._clear_metadata()
            return
        # selected[0] is scan_id
        # selected[1] is partial uid
        item = selected[1]
        child_node_path = item.text()
        model.on_item_selected(child_node_path)

        self.info_box.setText(model.info_text)
        self.open_button.setEnabled(model.open_button_enabled)

    def _on_item_double_click(self, item):
        # TODO: do we want users to be able to click into a run?
        # Maybe we should let the users pick the streams they want to plot
        # If no, we should disable this function
        # If yes, we need to be careful of the node_path_parts and
        # the state of the open button
        if item is self.catalog_breadcrumbs:
            self.model.exit_node()
            return
        self.model.open_node(item.text())
        self.open_button.setEnabled(False)

    def _on_load(self):
        selected = self.catalog_table.selectedItems()
        if not selected:
            return
        item = selected[1]
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

        if self.dialog.model.client is None:
            return
        self.model.url = self.dialog.model.client[*self.dialog.model.selected_catalog_path].uri

        _logger.debug(f"{self.model.url = }")

    def setDataSource(self, source):
        self.data = source
        self.model.url = self.data.client.uri
        _logger.debug(f'{type(self.data) = }; {self.data = }')
        selection = self.set_data_source_key()

        if selection is not None:
            # TODO: figure out how to let user pick stream
            dataObject = self._getDataObject(selection=selection, stream="primary")
            # self.graphWidget.setImageData(dataObject.data)
            self.lastDataObject = dataObject

    def set_data_source_key(self):
        if self.model.node_path_parts:
            self.selection = self.model.client[self.model.node_path_parts]
        else:
            self.selection = None
        _logger.debug(f"QTiledWidget {self.selection = }")
        return self.selection
    
    def _getDataObject(self, key=None, selection=None, stream="primary"):
        if key is None:
            # key = self.info['Key']
            _logger.debug('deal with later')
        dataObject = self.data.getDataObject(
            key,
            selection=selection,
            stream=stream,
        )
        # if dataObject is not None:
        #     dataObject.info['legend'] = self.info['Key']
        #     dataObject.info['imageselection'] = False
        #     dataObject.info['scanselection'] = False
        #     dataObject.info['targetwidgetid'] = id(self)
        #     self.data.addToPoller(dataObject)
        return dataObject

    def _on_add_clicked(self, *, emit=True):
        """Add plot to ScanWindow."""
        _logger.debug("QTiledWidget._on_add_clicked()...")
        selected = self.catalog_table.selectedItems()
        if not selected:
            return
        item = selected[1]
        selected_node_path_parts = self.model.node_path_parts + (item.text(),)
        sel_list = []
        channel_sel  = self.data_channel_table.getChannelSelection()
        _logger.debug(f'{channel_sel = }')
        _logger.debug(f'{self.model.node_path_parts = }')
        if len(channel_sel['Data Channel List']):
            if len(channel_sel['y']):
                sel = {
                    'SourceName': self.data.sourceName,
                    'SourceType': self.data.sourceType,
                    'Key': selected_node_path_parts,
                    'legend': '/'.join(selected_node_path_parts),
                    'selection': {'x': channel_sel['x'],
                                  'y': channel_sel['y'],
                                  'm': channel_sel['m'],
                                  'Channel List': channel_sel['Data Channel List']},
                    'scanselection': True,
                    }
                sel_list.append(sel)

        _logger.debug(f'{sel_list = }')
        _logger.debug(f'{emit = }')

        if emit:
            if len(sel_list):
                self.sigAddSelection.emit(sel_list)
            else:
                return sel_list

    def connect_model_signals(self) -> None:
        """Connect dialog slots to model signals."""
        _logger.debug("QTiledWidget.connect_model_signals()...")

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
            self._set_current_location_label()
            self.populate_run_table()
            self._rebuild_current_path_layout()

        self.model.url_changed.connect(self.model.on_url_changed)

    def connect_model_slots(self) -> None:
        """Connect model slots to dialog signals."""
        _logger.debug("QTiledWidget.connect_model_slots()...")

        model = self.model

        self.first_page.clicked.connect(model.on_first_page_clicked)
        self.next_page.clicked.connect(model.on_next_page_clicked)
        self.previous_page.clicked.connect(model.on_prev_page_clicked)
        self.last_page.clicked.connect(model.on_last_page_clicked)
        self.rows_per_page_selector.currentIndexChanged.connect(self.model.on_rows_per_page_changed)

    def connect_self_signals(self):
        _logger.debug("QTiledWidget.connect_self_signals()...")
        # TODO find another way to do this?
        self.select_tiled_catalog.clicked.connect(self.show_dialog)
        self.catalog_table.itemSelectionChanged.connect(self._on_item_selected)
        # self.catalog_table.itemDoubleClicked.connect(
        #     self._on_item_double_click
        # )
        self.open_button.clicked.connect(self._on_load)
        self.add_button.clicked.connect(self._on_add_clicked)


# # Command Buttons Connections
# addButton.clicked.connect(self._addClicked)
# replaceButton.clicked.connect(self._replaceClicked)
# removeButton.clicked.connect(self._removeClicked)