from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt, QSize
from app.ui.shared import get_icon

class Toolbar:
    @staticmethod
    def setup(parent_layout, window, initial_opacity):
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        window.open_button = QPushButton("Abrir Archivo", window)
        window.open_button.setToolTip("Abrir archivo de guión (.md, .pdf, .txt)\nAtajo: Ctrl + O")
        window.open_button.clicked.connect(window.open_script_file)
        button_row.addWidget(window.open_button)
        
        button_row.addStretch(1)

        opacity_label = QLabel("Opacidad:", window)
        opacity_label.setObjectName("statusLabel")
        button_row.addWidget(opacity_label)

        window.opacity_slider = QSlider(Qt.Horizontal, window)
        window.opacity_slider.setMinimum(20)
        window.opacity_slider.setMaximum(100)
        window.opacity_slider.setValue(int(initial_opacity * 100))
        window.opacity_slider.setFixedWidth(100)
        window.opacity_slider.setToolTip("Ajustar opacidad de la ventana (20-100%)")
        window.opacity_slider.valueChanged.connect(window._on_opacity_slider_changed)
        button_row.addWidget(window.opacity_slider)

        parent_layout.addLayout(button_row)

    @staticmethod
    def setup_autoscroll(parent_layout, window):
        row = QHBoxLayout()
        row.setSpacing(6)

        row.addStretch(1)

        window.scroll_play_btn = QPushButton("", window)
        window.scroll_play_btn.setObjectName("edgeButton")
        window.scroll_play_btn.setIcon(get_icon("play"))
        window.scroll_play_btn.setIconSize(QSize(14, 14))
        window.scroll_play_btn.setToolTip("Iniciar desplazamiento automático")
        window.scroll_play_btn.clicked.connect(window._toggle_autoscroll)
        row.addWidget(window.scroll_play_btn)

        window.scroll_slower_btn = QPushButton("", window)
        window.scroll_slower_btn.setObjectName("edgeButton")
        window.scroll_slower_btn.setIcon(get_icon("minus"))
        window.scroll_slower_btn.setIconSize(QSize(14, 14))
        window.scroll_slower_btn.setToolTip("Reducir velocidad")
        window.scroll_slower_btn.clicked.connect(window._autoscroll_slower)
        row.addWidget(window.scroll_slower_btn)

        window.scroll_speed_label = QLabel("3", window)
        window.scroll_speed_label.setObjectName("statusLabel")
        window.scroll_speed_label.setFixedWidth(20)
        window.scroll_speed_label.setAlignment(Qt.AlignCenter)
        row.addWidget(window.scroll_speed_label)

        window.scroll_faster_btn = QPushButton("", window)
        window.scroll_faster_btn.setObjectName("edgeButton")
        window.scroll_faster_btn.setIcon(get_icon("plus"))
        window.scroll_faster_btn.setIconSize(QSize(14, 14))
        window.scroll_faster_btn.setToolTip("Aumentar velocidad")
        window.scroll_faster_btn.clicked.connect(window._autoscroll_faster)
        row.addWidget(window.scroll_faster_btn)

        parent_layout.addLayout(row)
