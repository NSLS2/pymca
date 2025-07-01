import logging

from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, QThreadPool

from tiled.queries import FullText, Key, Regex


_logger = logging.getLogger(__name__)


class TiledSearchSignals(QObject):
    finished = pyqtSignal()
    search_results = pyqtSignal(object)


class TiledSearchRunnable(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        self.signals = TiledSearchSignals()
        self.run_kwargs = kwargs

    def run(self):
        if self.run_kwargs["search_type"] == "key_value":
            results = self.run_kwargs["client"].search(Key(self.run_kwargs["key"]) == self.run_kwargs["value"])
        elif self.run_kwargs["search_type"] == "full_text":
            results = self.run_kwargs["client"].search(FullText(self.run_kwargs["value"]))
        elif self.run_kwargs["search_type"] == "regex":
            results = self.run_kwargs["client"].search(Regex(self.run_kwargs["key"], pattern=self.run_kwargs["value"]))
        else:
            _logger.debug(f"Unknown search type {self.run_kwargs['search_type']}. Returning...")
            results = None
        _logger.debug(f"^^^^^^^^       {results}")
        self.signals.finished.emit()
        self.signals.search_results.emit(results)
