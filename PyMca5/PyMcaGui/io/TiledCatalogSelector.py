import logging
from collections import defaultdict
from typing import Callable, List, Mapping, Optional, Sequence
from urllib.parse import ParseResult, urlparse as _urlparse

from PyQt5.QtCore import QEvent, QObject, pyqtSignal

from tiled.client import from_uri
from tiled.client.base import BaseClient


_logger = logging.getLogger(__name__)


class TiledCatalogSelectorSignals(QObject):
    """Collection of signals for a TiledCatalogSelector model."""
    client_connected = pyqtSignal(
        str, # new URL
        str, # new API URL
        name="TiledCatalogSelector.client_connected",
    )
    
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)


class TiledCatalogSelector(object):
    """View Model for selecting a Tiled CatalogOfBlueskyRuns."""
    Signals = TiledCatalogSelectorSignals

    def __init__(
        self,
        /,
        url: str = None,
        client: BaseClient = None,
        validators: Mapping[str, List[Callable]] = None,
        parent: Optional[QObject] = None,
        *args,
        **kwargs,
    ):
        self.url = url
        self.client = client
        self.validators = defaultdict(list)

        self.signals = self.Signals(parent)
        self.client_connected = self.signals.client_connected

    def on_url_focus_in_event(self, event: QEvent):
        """Handle the event when the URL widget gains focus."""
        self._url_buffer = None

    def on_url_text_edited(self, new_text: str):
        """Handle a notification that the URL is being edited."""
        self._url_buffer = new_text

    def on_url_editing_finished(self):
        """Handle a notification that URL editing is complete."""
        try:
            for validate in self.validators["url"]:
                validate(self._url_buffer)
        except ValueError as exception:
            _logger.info(exception.msg)
            return
        
        self.url = self._url_buffer
        self._url_buffer = None

    def on_connect_clicked(self, checked: bool = False):
        """Handle a button click to connect to the Tiled client."""
        try:
            new_client = self.client_from_url(self.url)
        except Exception as exception:
            _logger.info(str(exception))
            # TODO: SHould we re-raise the exception or emit a signal to inform the viewer?
            return

        if self.client:
            # TODO: Clean-up previously connected client?
            ...

        self.client = new_client
        self.client_connected.emit(self.client.uri, self.client.context.api_uri)

    @staticmethod
    def client_from_url(url: str):
        """Create a Tiled client that is connected to the requested URL."""
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
