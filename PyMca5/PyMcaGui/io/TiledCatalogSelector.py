import functools
import logging
from collections import defaultdict
from typing import Callable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import ParseResult, urlparse as _urlparse

from PyQt5.QtCore import QObject, pyqtSignal

from tiled.client import from_uri
from tiled.client.base import BaseClient
from tiled.structures.core import StructureFamily


_logger = logging.getLogger(__name__)


class TiledCatalogSelectorSignals(QObject):
    """Collection of signals for a TiledCatalogSelector model."""
    client_connected = pyqtSignal(
        str, # new URL
        str, # new API URL
        name="TiledCatalogSelector.client_connected",
    )
    client_connection_error = pyqtSignal(
        str, # Error message
        name="TiledCatalogSelector.client_connection_error",
    )
    table_changed = pyqtSignal(
        tuple, # New node path parts, tuple of strings
        name="TiledCatalogSelector.table_changed",
    )
    url_changed = pyqtSignal(
        name="TiledCatalogSelector.url_changed",
    )
    url_validation_error = pyqtSignal(
        str, # Error message
        name="TiledCatalogSelector.url_validation_error",
    )
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)


class TiledCatalogSelector(object):
    """View Model for selecting a Tiled CatalogOfBlueskyRuns."""
    Signals = TiledCatalogSelectorSignals

    def __init__(
        self,
        /,
        url: str = "",
        client: BaseClient = None,
        validators: Mapping[str, List[Callable]] = None,
        parent: Optional[QObject] = None,
        *args,
        **kwargs,
    ):
        _logger.debug("TiledCatalogSelector.__init__()...")

        self._url = url
        self._client = client
        self.validators = defaultdict(list)
        if validators:
            self.validators.update(validators)

        self.signals = self.Signals(parent)
        self.client_connected = self.signals.client_connected
        self.client_connection_error = self.signals.client_connection_error
        self.table_changed = self.signals.table_changed
        self.url_changed = self.signals.url_changed
        self.url_validation_error = self.signals.url_validation_error

        # A buffer to receive updates while the URL is being edited
        self._url_buffer = self.url

    @property
    def url(self) -> str:
        """URL for accessing tiled server data."""
        return self._url
    
    @url.setter
    def url(self, value: str):
        """Updates the URL (and buffer) for accessing tiled server data.
        
            Emits the 'url_changed' signal.
        """
        old_value = self._url
        self._url = value
        self._url_buffer = value
        if value != old_value:
            self.url_changed.emit()

    @property
    def client(self):
        """Fetch the root Tiled client."""
        return self._client

    @client.setter
    def client(self, _):
        """Do not directly replace the root Tiled client."""
        raise NotImplementedError("Call set_root_client() instead")

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

    def on_url_text_edited(self, new_text: str):
        """Handle a notification that the URL is being edited."""
        _logger.debug("TiledCatalogSelector.on_url_text_edited()...")

        self._url_buffer = new_text

    def on_url_editing_finished(self):
        """Handle a notification that URL editing is complete."""
        _logger.debug("TiledCatalogSelector.on_url_editing_finished()...")

        new_url = self._url_buffer.strip()

        try:
            for validate in self.validators["url"]:
                validate(new_url)
        except ValueError as exception:
            error_message = str(exception)
            _logger.error(error_message)
            self.url_validation_error.emit(error_message)
            return
        
        self.url = new_url

    def on_connect_clicked(self, checked: bool = False):
        """Handle a button click to connect to the Tiled client."""
        _logger.debug("TiledCatalogSelector.on_connect_clicked()...")

        if self.client:
            # TODO: Clean-up previously connected client?
            ...

        self.connect_client()
        self.reset_client_view()

    def get_current_node(self) -> BaseClient:
        """Fetch a Tiled client corresponding to the current node path."""
        return self.get_node(self.node_path_parts)

    @functools.lru_cache(maxsize=1)
    def get_node(self, node_path_parts: Tuple[str]) -> BaseClient:
        """Fetch a Tiled client corresponding to the node path."""
        if node_path_parts:
            return self.client[node_path_parts]
        
        # An empty tuple indicates the root node
        return self.client

    def enter_node(self, child_node_path: str) -> None:
        """Select a child node within the current Tiled node.
        
            Emits the 'table_changed' signal."""
        self.node_path_parts += (child_node_path,)
        self._current_page = 0
        self.table_changed.emit(self.node_path_parts)

    def exit_node(self) -> None:
        """Select parent Tiled node.
        
            Emits the 'table_changed' signal."""
        self.node_path_parts = self.node_path_parts[:-1]
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

    @staticmethod
    def client_from_url(url: str):
        """Create a Tiled client that is connected to the requested URL."""
        _logger.debug("TiledCatalogSelector.client_from_url()...")

        return from_uri(url)


def urlparse(url: str) -> ParseResult:
    """Re-raise URL parsing errors with an extra custom message."""
    try:
        url_parts = _urlparse(url)
    except ValueError as exception:
        raise ValueError(f'{url} is not a valid URL.') from exception
    
    if not url_parts.scheme:
        raise ValueError(
            f'{url} is not a valid URL. URL must include a scheme.'
        )
    
    if not url_parts.netloc:
        raise ValueError(
            f'{url} is not a valid URL. URL must include a network location.'
        )
    
    return url_parts


def validate_url_syntax(url: str) -> None:
    """Verify that input string is parseable as a URL."""
    urlparse(url)


def validate_url_scheme(
    url: str,
    valid_schemes: Sequence[str] = ("http", "https"),
) -> None:
    """Verify that URL scheme is one of 'valid_schemes'."""
    url_parts = urlparse(url)
    
    if url_parts.scheme not in valid_schemes:
        error_message = " ".join((
            f'{url} is not a valid Tiled URL.',
            "URL must start with",
            " or ".join(valid_schemes),
            "."
        ))
        raise ValueError(error_message)
