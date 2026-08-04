from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt, QSize
from app.ui.shared import get_icon

class Toolbar:
    @staticmethod
    def setup(parent_layout, window, initial_opacity):
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        window.open_button = QPushButton("Abrir Archivo", window)
        window.open_button.setToolTip("Abrir archivo de guion (.md, .pdf, .txt)\nAtajo: Ctrl + O")
        window.open_button.clicked.connect(window.open_script_file)
        button_row.addWidget(window.open_button)
        
        button_row.addStretch(1)

        opacity_label = QLabel("Opacidad:", window)
        button_row.addWidget(opacity_label)
        window._opacity_label = opacity_label

        window.opacity_slider = QSlider(Qt.Horizontal, window)
        window.opacity_slider.setRange(20, 100)
        window.opacity_slider.setValue(initial_opacity)
        window.opacity_slider.setFixedWidth(100)
        window.opacity_slider.setObjectName("opacitySlider")
        window.opacity_slider.setToolTip("Ajustar opacidad (20-100%)")
        window.opacity_slider.valueChanged.connect(window._on_opacity_slider_changed)
        button_row.addWidget(window.opacity_slider)

        window.opacity_pct_label = QLabel(f"{initial_opacity}%", window)
        window.opacity_pct_label.setToolTip("Opacidad actual")
        window.opacity_pct_label.setFixedWidth(36)
        button_row.addWidget(window.opacity_pct_label)

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
        window.scroll_play_btn.setToolTip("Iniciar desplazamiento automático\nAtajo: Espacio")
        window.scroll_play_btn.clicked.connect(window._toggle_autoscroll)
        row.addWidget(window.scroll_play_btn)

        window.scroll_slower_btn = QPushButton("", window)
        window.scroll_slower_btn.setObjectName("edgeButton")
        window.scroll_slower_btn.setIcon(get_icon("minus"))
        window.scroll_slower_btn.setIconSize(QSize(14, 14))
        window.scroll_slower_btn.setToolTip("Reducir velocidad\nAtajo: ↓")
        window.scroll_slower_btn.clicked.connect(window._autoscroll_slower)
        row.addWidget(window.scroll_slower_btn)

        window.scroll_speed_label = QLabel("3", window)
        window.scroll_speed_label.setObjectName("statusLabel")
        window.scroll_speed_label.setFixedWidth(24)
        window.scroll_speed_label.setAlignment(Qt.AlignCenter)
        row.addWidget(window.scroll_speed_label)

        window.scroll_faster_btn = QPushButton("", window)
        window.scroll_faster_btn.setObjectName("edgeButton")
        window.scroll_faster_btn.setIcon(get_icon("plus"))
        window.scroll_faster_btn.setIconSize(QSize(14, 14))
        window.scroll_faster_btn.setToolTip("Aumentar velocidad\nAtajo: ↑")
        window.scroll_faster_btn.clicked.connect(window._autoscroll_faster)
        row.addWidget(window.scroll_faster_btn)

        window.scroll_status_label = QLabel("⏸ Pausado", window)
        window.scroll_status_label.setObjectName("statusLabel")
        row.addWidget(window.scroll_status_label)

        parent_layout.addLayout(row)

    @staticmethod
    def setup_reading_overlay(parent, window):
        """Barra de lectura flotante: play/pause, velocidad y progreso."""
        from PyQt5.QtWidgets import QFrame
        overlay = QFrame(parent)
        overlay.setObjectName("readingOverlay")
        overlay_layout = QHBoxLayout(overlay)
        overlay_layout.setContentsMargins(8, 4, 8, 4)
        overlay_layout.setSpacing(6)

        window.reading_play_btn = QPushButton("", window)
        window.reading_play_btn.setObjectName("edgeButton")
        window.reading_play_btn.setIcon(get_icon("play"))
        window.reading_play_btn.setIconSize(QSize(14, 14))
        window.reading_play_btn.setToolTip("Reproducir desplazamiento\nAtajo: Espacio")
        window.reading_play_btn.clicked.connect(window._toggle_autoscroll)
        overlay_layout.addWidget(window.reading_play_btn)

        window.reading_slower_btn = QPushButton("", window)
        window.reading_slower_btn.setObjectName("edgeButton")
        window.reading_slower_btn.setIcon(get_icon("minus"))
        window.reading_slower_btn.setIconSize(QSize(14, 14))
        window.reading_slower_btn.setToolTip("Reducir velocidad\nAtajo: ↓")
        window.reading_slower_btn.clicked.connect(window._autoscroll_slower)
        overlay_layout.addWidget(window.reading_slower_btn)

        window.reading_speed_label = QLabel("3", window)
        window.reading_speed_label.setObjectName("statusLabel")
        window.reading_speed_label.setFixedWidth(24)
        window.reading_speed_label.setAlignment(Qt.AlignCenter)
        overlay_layout.addWidget(window.reading_speed_label)

        window.reading_faster_btn = QPushButton("", window)
        window.reading_faster_btn.setObjectName("edgeButton")
        window.reading_faster_btn.setIcon(get_icon("plus"))
        window.reading_faster_btn.setIconSize(QSize(14, 14))
        window.reading_faster_btn.setToolTip("Aumentar velocidad\nAtajo: ↑")
        window.reading_faster_btn.clicked.connect(window._autoscroll_faster)
        overlay_layout.addWidget(window.reading_faster_btn)

        overlay_layout.addStretch(1)

        window.reading_progress_label = QLabel("", window)
        window.reading_progress_label.setObjectName("statusLabel")
        overlay_layout.addWidget(window.reading_progress_label)

        window.reading_restart_btn = QPushButton("", window)
        window.reading_restart_btn.setObjectName("edgeButton")
        window.reading_restart_btn.setIcon(get_icon("refresh"))
        window.reading_restart_btn.setIconSize(QSize(14, 14))
        window.reading_restart_btn.setToolTip("Volver al inicio y reiniciar")
        window.reading_restart_btn.clicked.connect(window._restart_autoscroll)
        window.reading_restart_btn.hide()
        overlay_layout.addWidget(window.reading_restart_btn)

        overlay.hide()
        return overlay
