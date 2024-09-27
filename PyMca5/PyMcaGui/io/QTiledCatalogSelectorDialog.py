import logging
from collections import defaultdict
from typing import Callable, Mapping, Optional

from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
    QApplication, QMainWindow,
)

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
        self.reset_url_entry()

    def create_layout(self) -> None:
        """Create the visual layout of widgets for the dialog."""
        _logger.debug("QTiledCatalogSelectorDialog.create_layout()...")

        # Connection elements
        self.url_entry = QLineEdit()
        self.connect_button = QPushButton("Connect")
        self.connection_label = QLabel("No url connected")

        # Connection layout
        connection_layout = QVBoxLayout()
        connection_layout.addWidget(self.url_entry)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.connection_label)
        connection_layout.addStretch()
        self.setLayout(connection_layout)

    def reset_url_entry(self) -> None:
        """Reset the stated of the url_entry widget."""
        _logger.debug("QTiledCatalogSelectorDialog.reset_url_entry()...")

        if not self.model.url:
            self.url_entry.setPlaceholderText("Enter a url")
        else:
            self.url_entry.setText(self.model.url)

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

    def initialize_values(self) -> None:
        """Initialize widget values."""
        self.reset_url_entry()

if __name__ == '__main__':
    from sys import argv
    app = QApplication(argv)
    window = QMainWindow()
    model = TiledCatalogSelector(parent=app)
    # model.url = "https://tiled-demo.blueskyproject.io/api"
    dialog = QTiledCatalogSelectorDialog(model=model)

    window.show()
    window.setCentralWidget(dialog)
    # breakpoint()
    exit(app.exec_())
