from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from .TiledCatalogSelector import TiledCatalogSelector


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
        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.create_layout()

    def create_layout(self) -> None:
        """Create the visual layout of widgets for the dialog."""
        # Connection elements
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Enter a url")
        self.connect_button = QPushButton("Connect")
        self.connection_label = QLabel("No url connected")

        # Connection layout
        connection_layout = QVBoxLayout()
        connection_layout.addWidget(self.url_entry)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(self.connection_label)
        connection_layout.addStretch()
        self.setLayout(connection_layout)
        