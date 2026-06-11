from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtCore import QSize
from app.ui.shared import get_icon

class HeaderBar:
    @staticmethod
    def setup(parent_layout, window):
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)

        window.capture_button = QPushButton(window)
        window.capture_button.setObjectName("edgeButton")
        window.capture_button.setIconSize(QSize(14, 14))
        window.capture_button.setText("")
        window.capture_button.clicked.connect(window.toggle_capture_visibility)

        window.edge_button = QPushButton(window)
        window.edge_button.setObjectName("edgeButton")
        window.edge_button.setIconSize(QSize(14, 14))
        window.edge_button.setText("")
        window.edge_button.clicked.connect(window.toggle_collapsed)

        header_row.addWidget(window.capture_button, 0)
        header_row.addWidget(window.edge_button, 0)
        parent_layout.addLayout(header_row)
