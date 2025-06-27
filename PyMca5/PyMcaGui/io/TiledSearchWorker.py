import logging
from typing import Callable, Mapping, Optional, Tuple

from tiled.client.base import BaseClient
from tiled.queries import FullText, Key, Regex

from PyQt5.QtCore import pyqtSignal, QObject, QThread


_logger = logging.getLogger(__name__)


class TiledSearchWorker(QObject):
    finished = pyqtSignal()
    search_results = pyqtSignal(object)

    def search(self, client: BaseClient, key: str, value: str, search_type: str):
        if search_type == "key_value":
            results = client.search(Key(key) == value)
        elif search_type == "full_text":
            results = client.search(FullText(value))
        elif search_type == "regex":
            results = client.search(Regex(key, pattern=value))
        else:
            _logger.debug(f"Unknown search type {search_type}. Returning...")
            results = None
        print(f"^^^^^^^^       {results}")
        self.finished.emit()
        self.search_results.emit(results)
        # return results
