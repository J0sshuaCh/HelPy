from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSlider
from PyQt5.QtCore import QSize, Qt
from app.ui.shared import get_icon

class PositionBar(QWidget):
    def __init__(self, initial_opacity=100, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.pos_left_btn = QPushButton("", self)
        self.pos_left_btn.setObjectName("edgeButton")
        self.pos_left_btn.setIcon(get_icon("arrow_left"))
        self.pos_left_btn.setIconSize(QSize(14, 14))
        self.pos_left_btn.setToolTip("Mover ventana al borde izquierdo")
        
        self.pos_center_btn = QPushButton("", self)
        self.pos_center_btn.setObjectName("edgeButton")
        self.pos_center_btn.setIcon(get_icon("arrow_up"))
        self.pos_center_btn.setIconSize(QSize(14, 14))
        self.pos_center_btn.setToolTip("Centrar ventana en la parte superior")
        
        self.pos_right_btn = QPushButton("", self)
        self.pos_right_btn.setObjectName("edgeButton")
        self.pos_right_btn.setIcon(get_icon("arrow_right"))
        self.pos_right_btn.setIconSize(QSize(14, 14))
        self.pos_right_btn.setToolTip("Mover ventana al borde derecho")
    
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(initial_opacity)
        self.opacity_slider.setFixedWidth(100)
        self.opacity_slider.setObjectName("opacitySlider")
        self.opacity_slider.setToolTip("Ajustar opacidad de la ventana (20-100%)")
        
        self.layout.addWidget(self.pos_left_btn)
        self.layout.addWidget(self.pos_center_btn)
        self.layout.addWidget(self.pos_right_btn)
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel("Opacidad:"))
        self.layout.addWidget(self.opacity_slider)

    def reload_icons(self):
        self.pos_left_btn.setIcon(get_icon("arrow_left"))
        self.pos_center_btn.setIcon(get_icon("arrow_up"))
        self.pos_right_btn.setIcon(get_icon("arrow_right"))
