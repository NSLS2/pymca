import logging
from typing import Callable, Mapping, Optional, Tuple

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


class QTiledSearchWidget(QWidget):
    def __init__(
        self,
        model: TiledRunSelector,
        parent: Optional[QWidget] = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize."""
        print("QTiledSearchWidget.__init__()")

        super().__init__(parent, *args, **kwargs)
        self.model = model

        self.key_label = QLabel("Key")
        self.key_text_edit = QLineEdit()
        value_label = QLabel("Value")
        value_text_edit = QLineEdit()
        self.full_text_checkbox = QCheckBox("Full text search")
        self.regex_checkbox = QCheckBox("Use RegEx pattern")
        self.full_text_advice = QLabel("Whole words only")
        self.full_text_advice.setVisible(False)

        layout = QGridLayout()
        # widget, row, column
        layout.addWidget(self.key_label, 0, 0)
        layout.addWidget(self.key_text_edit, 0, 1)
        layout.addWidget(value_label, 0, 2)
        layout.addWidget(value_text_edit, 0, 3)
        # widget, row, column, row span, column span
        layout.addWidget(self.full_text_checkbox, 1, 0, 1, 2)
        layout.addWidget(self.regex_checkbox, 1, 2, 1, 2)
        layout.addWidget(self.full_text_advice, 1, 2, 1, 2)

        self.setLayout(layout)

        self.full_text_checkbox.clicked.connect(self.on_full_text_checkbox_checked)
        self.regex_checkbox.clicked.connect(self.on_regex_checkbox_checked)

    def on_full_text_checkbox_checked(self):
        self.regex_checkbox.setVisible(not self.regex_checkbox.isVisible())
        self.full_text_advice.setVisible(not self.full_text_advice.isVisible())

    def on_regex_checkbox_checked(self):
        self.key_label.setEnabled(not self.key_label.isEnabled())
        self.key_text_edit.setEnabled(not self.key_text_edit.isEnabled())
        self.full_text_checkbox.setEnabled(not self.full_text_checkbox.isEnabled())


if __name__ == "__main__":
    from sys import argv
    from PyQt5.QtWidgets import QApplication, QMainWindow

    app = QApplication(argv)
    window = QMainWindow()
    model = TiledRunSelector(parent=app)
    model.url = "https://tiled-demo.blueskyproject.io/api"
    widget = QTiledSearchWidget(model=model)

    window.show()
    window.setCentralWidget(widget)
    # breakpoint()
    exit(app.exec_())
