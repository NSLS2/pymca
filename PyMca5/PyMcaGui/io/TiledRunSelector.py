import functools
from math import ceil
import logging
from collections import defaultdict
from datetime import date, datetime
import json
from typing import Callable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import ParseResult, urlparse as _urlparse

from PyQt5.QtCore import QObject, pyqtSignal
# from PyQt5.QtWidgets import QApplication

from tiled.client import from_uri
from tiled.client.base import BaseClient
from tiled.structures.core import StructureFamily


_logger = logging.getLogger(__name__)


def json_decode(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


class TiledRunSelectorSignals(QObject):
    """Collection of signals for a TiledRunSelector model."""
    client_connected = pyqtSignal(
        str, # new URL
        str, # new API URL
        name="TiledRunSelector.client_connected",
    )
    client_connection_error = pyqtSignal(
        str, # Error message
        name="TiledRunSelector.client_connection_error",
    )
    refresh_client = pyqtSignal(
        name="TiledRunSelector.refresh_client",
    )
    table_changed = pyqtSignal(
        tuple, # New node path parts, tuple of strings
        name="TiledRunSelector.table_changed",
    )
    url_changed = pyqtSignal(
        name="TiledRunSelector.url_changed",
    )
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)


class TiledRunSelector(object):
    """View Model for selecting a Tiled CatalogOfBlueskyRuns."""
    Signals = TiledRunSelectorSignals
    SUPPORTED_TYPES = (StructureFamily.array, StructureFamily.container)

    def __init__(
        self,
        /,
        url: str = "",
        client: BaseClient = None,
        validators: Mapping[str, List[Callable]] = None,
        parent: Optional[QObject] = None,
        rows_per_page_options: Optional[List[int]] = None,
        *args,
        **kwargs,
    ):
        _logger.debug("TiledRunSelector.__init__()...")

        self._url = url
        self._client = client
        self.validators = defaultdict(list)
        if validators:
            self.validators.update(validators)

        self.signals = self.Signals(parent)
        self.client_connected = self.signals.client_connected
        self.client_connection_error = self.signals.client_connection_error
        self.refresh_client = self.signals.refresh_client
        self.table_changed = self.signals.table_changed
        self.url_changed = self.signals.url_changed

        self.node_path_parts = ()
        self._current_page = 0
        if rows_per_page_options is None:
            self._rows_per_page_options = [5, 10, 25]
        else:
            self._rows_per_page_options = rows_per_page_options
        self._rows_per_page_index = 0
        self.selected_run_path = ()

    @property
    def url(self) -> str:
        """URL for accessing tiled server data."""
        return self._url
    
    @url.setter
    def url(self, value: str):
        """Updates the URL for accessing tiled server data.
        
            Emits the 'url_changed' signal.
        """
        old_value = self._url
        self._url = value
        if value != old_value:
            self.url_changed.emit()

    @property
    def client(self):
        """Fetch the root Tiled client."""
        return self._client

    @client.setter
    def client(self, _):
        """Do not directly replace the root Tiled client."""
        raise NotImplementedError("Call connect_client() instead")
    
    @property
    def rows_per_page(self):
        return self._rows_per_page_options[self._rows_per_page_index]

    def connect_client(self) -> None:
        """Connect the model's Tiled client to the Tiled server at URL.
        
            Emits the 'client_connection_error' signal when client does not connect.
        """
        try:
            new_client = self.client_from_url(self.url)
        except Exception as exception:
            error_message = str(exception)
            _logger.error(error_message)
            self.client_connection_error.emit(error_message)
            return

        self._client = new_client
        self.client_connected.emit(self._client.uri, str(self._client.context.api_uri))

    def reset_client_view(self) -> None:
        """Prepare the model to receive content from a Tiled server.
        
            Emits the 'table_changed' signal when a client is defined.
        """
        self.node_path_parts = ()
        self._current_page = 0
        if self.client is not None:
            self.table_changed.emit(self.node_path_parts)

    def on_url_changed(self, checked: bool = False):
        """Handle a button click to connect to the Tiled client."""
        _logger.debug("TiledRunSelector.on_connect_clicked()...")

        if self.client:
            # TODO: Clean-up previously connected client?
            ...

        self.connect_client()
        self.reset_client_view()

    def is_catalog_of_bluesky_runs(self, node):
        specs = node.item["attributes"]["specs"]
        for spec in specs:
            if spec["name"] == "CatalogOfBlueskyRuns":
                return True
            else:
                pass
        return False

    def on_item_selected(self, child_node_path):
        node_path_parts = self.node_path_parts + (child_node_path,)
        node = self.get_node(node_path_parts)
        # Don't update model.node_path_parts here
        # If model.node_path_parts gets updated here, the navigation
        # buttons think we are inside the run

        self.open_button_enabled = True

        attrs = node.item["attributes"]        
        family = attrs["structure_family"]
        metadata = json.dumps(attrs["metadata"], indent=2, default=json_decode)

        # TODO: this metadata is hard to read in the info box
        info = f"<b>type:</b> {family}<br>"
        if family == StructureFamily.array:
            shape = attrs["structure"]["shape"]
            info += f"<b>shape:</b> {tuple(shape)}<br>"
        info += f"<b>metadata:</b> <pre>{metadata}</pre>"
        
        self.info_text = info
    
    def open_run(self, child_node_path):
        self.selected_run_path = self.node_path_parts + (child_node_path,)

    def on_rows_per_page_changed(self, index):
        self._rows_per_page_index = index
        self._current_page = 0
        self.table_changed.emit(self.node_path_parts)

    def on_first_page_clicked(self):
        self._current_page = 0
        self.table_changed.emit(self.node_path_parts)

    def on_prev_page_clicked(self):
        if self._current_page != 0:
            self._current_page -= 1
            self.table_changed.emit(self.node_path_parts)

    def on_next_page_clicked(self):
        rows_per_page = self.rows_per_page
        if (
            self._current_page * rows_per_page
        ) + rows_per_page < len(self.get_current_node()):
            self._current_page += 1
            self.table_changed.emit(self.node_path_parts)

    def on_last_page_clicked(self):
        # NOTE: math.ceil gives the wrong answer for really large numbers
        # Solution 4 in this answer: https://stackoverflow.com/a/54585138
        self._current_page = ceil(len(self.get_current_node()) / self.rows_per_page) - 1
        self.table_changed.emit(self.node_path_parts)

    def get_current_node(self) -> BaseClient:
        """Fetch a Tiled client corresponding to the current node path."""
        return self.get_node(self.node_path_parts)

    @functools.lru_cache(maxsize=1)
    def get_node(self, node_path_parts: Tuple[str]) -> BaseClient:
        """Fetch a Tiled client corresponding to the node path."""
        # NOTE: Passing tiled a tuple returns a list of bluesky runs
        # even if there is only one item in the tuple
        # This may change in the future when the capibility to pass a list
        # of uids to tiled is removed
        if node_path_parts:
            return self.client[node_path_parts[0]]
        
        # An empty tuple indicates the root node
        return self.client

    def enter_node(self, child_node_path: str) -> None:
        """Select a child node within the current Tiled node.
        
            Emits the 'table_changed' signal."""
        _logger.info("Entering node...")
        self.node_path_parts += (child_node_path,)
        self._current_page = 0
        self.table_changed.emit(self.node_path_parts)

    def exit_node(self) -> None:
        """Select parent Tiled node.
        
            Emits the 'table_changed' signal."""
        _logger.info("Exiting node...")
        self.node_path_parts = self.node_path_parts[:-1]
        self._current_page = 0
        self.table_changed.emit(self.node_path_parts)

    def jump_to_node(self, index) -> None:
        """Select parent Tiled node.
        
            Emits the 'table_changed' signal."""
        _logger.info(f"Jumping to node at index {index}...")
        self.node_path_parts = self.node_path_parts[:index]
        self._current_page = 0
        self.table_changed.emit(self.node_path_parts)

    def open_node(self, child_node_path: str) -> None:
        """Select a child node if its Tiled structure_family is supported."""
        node = self.get_current_node()[child_node_path]
        family = node.item["attributes"]["structure_family"]

        if family == StructureFamily.array:
            _logger.info("Found array, plotting TODO")
            ...
        elif family == StructureFamily.container:
            self.enter_node(child_node_path)
        else:
            _logger.error(f"StructureFamily not supported:'{family}")
            # TODO: Emit an error signal for dialog widget to respond to

    def on_refresh_client(self):
        """Update content from Tiled server."""
        if self.client is None:
            return
        self.client.refresh()
        self.table_changed.emit(self.node_path_parts)
        # QApplication.processEvents()

    @staticmethod
    def client_from_url(url: str):
        """Create a Tiled client that is connected to the requested URL."""
        _logger.debug("TiledRunSelector.client_from_url()...")

        return from_uri(url)
