from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt5.QtCore import QSize
from app.ui.shared import get_icon

class HeaderBar:
    @staticmethod
    def setup(parent_layout, window):
        header_widget = QWidget(window)
        header_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_row = QHBoxLayout(header_widget)
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)

        window.capture_button = QPushButton(window)
        window.capture_button.setObjectName("edgeButton")
        window.capture_button.setIconSize(QSize(14, 14))
        window.capture_button.setText("")
        window.capture_button.setToolTip("Mostrar/ocultar ventana en capturas de pantalla")
        window.capture_button.clicked.connect(window.toggle_capture_visibility)

        window.edge_button = QPushButton(window)
        window.edge_button.setObjectName("edgeButton")
        window.edge_button.setIconSize(QSize(14, 14))
        window.edge_button.setText("")
        window.edge_button.setToolTip("Colapsar/expandir panel de guiones")
        window.edge_button.clicked.connect(window.toggle_collapsed)

        header_row.addWidget(window.capture_button, 0)
        header_row.addWidget(window.edge_button, 0)
        header_widget.setFixedHeight(header_widget.sizeHint().height())
        parent_layout.addWidget(header_widget)
