from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt

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
