import logging
from typing import Callable, Mapping, Optional, Tuple

from PyQt5.QtCore import QThreadPool, QTimer
from PyQt5.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from PyMca5.PyMcaGui.io.TiledRunSelector import TiledRunSelector
from PyMca5.PyMcaGui.io.TiledSearchWorker import TiledSearchRunnable


_logger = logging.getLogger(__name__)


class QTiledSearchWidget(QWidget):
    def __init__(
        self,
        model: TiledRunSelector,
        parent: Optional[QWidget] = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize."""
        _logger.debug("QTiledSearchWidget.__init__()")

        super().__init__(parent, *args, **kwargs)
        self.model = model

        self.thread_pool = QThreadPool.globalInstance()

        self.key_label = QLabel("Key")
        self.key_entry = QLineEdit()
        self.key_entry.setClearButtonEnabled(True)
        self.value_label = QLabel("Value")
        self.value_entry = QLineEdit()
        self.value_entry.setClearButtonEnabled(True)
        self.full_text_checkbox = QCheckBox("Full text search")
        self.regex_checkbox = QCheckBox("Use RegEx pattern")
        self.full_text_hint = QLabel("Whole words only")
        self.full_text_hint.setVisible(False)

        layout = QGridLayout()
        # widget, row, column
        layout.addWidget(self.key_label, 0, 0)
        layout.addWidget(self.key_entry, 0, 1)
        layout.addWidget(self.value_label, 0, 2)
        layout.addWidget(self.value_entry, 0, 3)
        # widget, row, column, row span, column span
        layout.addWidget(self.full_text_checkbox, 1, 0, 1, 2)
        layout.addWidget(self.regex_checkbox, 1, 2, 1, 2)
        layout.addWidget(self.full_text_hint, 1, 2, 1, 2)

        self.setLayout(layout)

        self.full_text_checkbox.clicked.connect(self.on_full_text_checkbox_checked)
        self.regex_checkbox.clicked.connect(self.on_regex_checkbox_checked)

        self.debounce = QTimer()
        self.debounce.setInterval(1000)
        self.debounce.setSingleShot(True)
        self.debounce.timeout.connect(self.debounced_search)

        self.key_entry.textChanged.connect(self.debounce.start)
        self.value_entry.textChanged.connect(self.debounce.start)

    def _search(self):
        key = self.key_entry.text()
        _logger.debug(f"Key: {key}")
        value = self.value_entry.text()
        _logger.debug(f"Value: {value}")
        _logger.debug("Searching...")
        full_text_enabled = self.full_text_checkbox.isChecked()
        regex_enabled = self.regex_checkbox.isChecked()
        # FullText search - full text check and non empty value
        if value != "" and full_text_enabled:
            search_type = "full_text"
            key = None
        # RegEx search - regex check and non empty key and value
        elif (key != "" and value != "") and regex_enabled:
            search_type = "regex"
        # key value search - no checks and non empty key and value
        elif (key != "" and value != "") and not (full_text_enabled or regex_enabled):
            search_type = "key_value"
        # every other combo should not search
        else:
            search_type = "no_search"
        runnable = TiledSearchRunnable(client=self.model.client, key=key, value=value, search_type=search_type)
        runnable.signals.search_results.connect(self.on_search_results)
        self.thread_pool.start(runnable)
        return search_type
    
    def on_search_results(self, results):
        _logger.debug("on_search_results")
        _logger.debug(f"        {results = }")
        self.model.search_results = results
        # Reset current page to 0 so we don't end up at an impossible index
        self.model._current_page = 0
        self.model.table_changed.emit(self.model.node_path_parts)

    def debounced_search(self):
        self._search()

    def on_full_text_checkbox_checked(self):
        self.regex_checkbox.setVisible(not self.regex_checkbox.isVisible())
        self.full_text_hint.setVisible(not self.full_text_hint.isVisible())
        self.key_label.setEnabled(not self.key_label.isEnabled())
        self.key_entry.setEnabled(not self.key_entry.isEnabled())
        self._search()

    def on_regex_checkbox_checked(self):
        self.full_text_checkbox.setEnabled(not self.full_text_checkbox.isEnabled())
        self._search()


if __name__ == "__main__":
    from sys import argv
    from PyQt5.QtWidgets import QApplication, QMainWindow

    app = QApplication(argv)
    window = QMainWindow()
    model = TiledRunSelector(parent=app)
    model.url = "https://tiled-demo.blueskyproject.io/api/v1/metadata/bmm/raw"
    model.connect_client()
    widget = QTiledSearchWidget(model=model)

    window.show()
    window.setCentralWidget(widget)
    # breakpoint()
    exit(app.exec_())
