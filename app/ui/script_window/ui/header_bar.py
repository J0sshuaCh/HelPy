from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy, QLabel
from PyQt5.QtCore import QSize, Qt
from app.ui.shared import get_icon
from app.ui.shared.icons import get_logo_pixmap

class HeaderBar:
    @staticmethod
    def setup(parent_layout, window):
        header_widget = QWidget(window)
        header_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_row = QHBoxLayout(header_widget)
        header_row.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel()
        logo_label.setPixmap(get_logo_pixmap(38, 20))
        logo_label.setFixedHeight(20)
        header_row.addWidget(logo_label)

        title_label = QLabel("HelPy – Guion")
        title_label.setObjectName("appTitle")
        header_row.addWidget(title_label)

        header_row.addStretch(1)

        window.capture_button = QPushButton("", window)
        window.capture_button.setObjectName("edgeButton")
        window.capture_button.setIconSize(QSize(14, 14))
        window.capture_button.setToolTip("Mostrar/ocultar en capturas\nAtajo: Ctrl + Shift + C")
        window.capture_button.clicked.connect(window.toggle_capture_visibility)

        window.panel_toggle_button = QPushButton("", window)
        window.panel_toggle_button.setObjectName("edgeButton")
        window.panel_toggle_button.setIcon(get_icon("panels"))
        window.panel_toggle_button.setIconSize(QSize(14, 14))
        window.panel_toggle_button.setToolTip("Mostrar/ocultar controles\nAtajo: Ctrl + P")
        window.panel_toggle_button.clicked.connect(window._toggle_control_panel)

        window.help_button = QPushButton("", window)
        window.help_button.setObjectName("edgeButton")
        window.help_button.setIcon(get_icon("help"))
        window.help_button.setIconSize(QSize(14, 14))
        window.help_button.setToolTip("Mostrar atajos de teclado\nAtajo: ?")
        window.help_button.clicked.connect(window._show_shortcuts)

        window.edge_button = QPushButton("", window)
        window.edge_button.setObjectName("edgeButton")
        window.edge_button.setIconSize(QSize(14, 14))
        window.edge_button.setToolTip("Colapsar/expandir panel\nAtajo: Ctrl + H")
        window.edge_button.clicked.connect(window.toggle_collapsed)

        header_row.addWidget(window.capture_button, 0)
        header_row.addWidget(window.panel_toggle_button, 0)
        header_row.addWidget(window.help_button, 0)
        header_row.addWidget(window.edge_button, 0)
        header_widget.setFixedHeight(header_widget.sizeHint().height())
        parent_layout.addWidget(header_widget)
