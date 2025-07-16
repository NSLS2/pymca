from PyQt5.QtCore import pyqtSignal, QObject, QRunnable


class TiledWorkerSignals(QObject):
    finished = pyqtSignal()
    results = pyqtSignal(object)


class TiledWorker(QRunnable):
    def __init__(self, **kwargs):
        super().__init__()
        self.signals = TiledWorkerSignals()
        self.rows_per_page = kwargs["rows_per_page"]
        self.current_page = kwargs["current_page"]
        self.client = kwargs["client"]
        self.search_results = kwargs["search_results"]
        self.node_path_parts = kwargs["node_path_parts"]

    def run(self):
        if self.search_results is None:
            catalog_or_search_results = self.client
        else:
            catalog_or_search_results = self.search_results
        node_offset = self.rows_per_page * self.current_page
        if self.node_path_parts:
            results = catalog_or_search_results[self.node_path_parts[0]].items()[node_offset: node_offset + self.rows_per_page]
        else:
            results = catalog_or_search_results.items()[node_offset: node_offset + self.rows_per_page]
        self.signals.finished.emit()
        self.signals.results.emit(results)
