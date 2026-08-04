from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QButtonGroup
from PyQt5.QtCore import QSize, Qt
from app.ui.shared import get_icon

class PositionBar(QWidget):
    def __init__(self, settings, initial_opacity=100, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.body = QFrame(self)
        self.body.setObjectName("positionBody")
        body_layout = QHBoxLayout(self.body)
        body_layout.setContentsMargins(0, 4, 0, 0)
        body_layout.setSpacing(6)

        self.pos_left_btn = QPushButton("", self)
        self.pos_left_btn.setObjectName("edgeButton")
        self.pos_left_btn.setCheckable(True)
        self.pos_left_btn.setIcon(get_icon("arrow_left"))
        self.pos_left_btn.setIconSize(QSize(14, 14))
        self.pos_left_btn.setToolTip("Mover ventana al borde izquierdo")
        
        self.pos_center_btn = QPushButton("", self)
        self.pos_center_btn.setObjectName("edgeButton")
        self.pos_center_btn.setCheckable(True)
        self.pos_center_btn.setIcon(get_icon("arrow_up"))
        self.pos_center_btn.setIconSize(QSize(14, 14))
        self.pos_center_btn.setToolTip("Centrar ventana en la parte superior")
        
        self.pos_right_btn = QPushButton("", self)
        self.pos_right_btn.setObjectName("edgeButton")
        self.pos_right_btn.setCheckable(True)
        self.pos_right_btn.setIcon(get_icon("arrow_right"))
        self.pos_right_btn.setIconSize(QSize(14, 14))
        self.pos_right_btn.setToolTip("Mover ventana al borde derecho")

        self._pos_group = QButtonGroup(self)
        self._pos_group.setExclusive(True)
        self._pos_group.addButton(self.pos_left_btn, 0)
        self._pos_group.addButton(self.pos_center_btn, 1)
        self._pos_group.addButton(self.pos_right_btn, 2)
    
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(initial_opacity)
        self.opacity_slider.setFixedWidth(100)
        self.opacity_slider.setObjectName("opacitySlider")
        self.opacity_slider.setToolTip("Ajustar opacidad de la ventana (20-100%)")
        
        body_layout.addWidget(self.pos_left_btn)
        body_layout.addWidget(self.pos_center_btn)
        body_layout.addWidget(self.pos_right_btn)
        body_layout.addStretch(1)
        body_layout.addWidget(QLabel("Opacidad:"))
        body_layout.addWidget(self.opacity_slider)

        self.opacity_pct_label = QLabel(f"{initial_opacity}%", self)
        self.opacity_pct_label.setToolTip("Opacidad actual")
        self.opacity_pct_label.setFixedWidth(36)
        body_layout.addWidget(self.opacity_pct_label)
        outer.addWidget(self.body)

    def reload_icons(self):
        self.pos_left_btn.setIcon(get_icon("arrow_left"))
        self.pos_center_btn.setIcon(get_icon("arrow_up"))
        self.pos_right_btn.setIcon(get_icon("arrow_right"))

    def set_active_position(self, mode: str):
        """Marca el botón de posición activa (izquierda, centro, derecha)."""
        btn = {"left": self.pos_left_btn, "center": self.pos_center_btn, "right": self.pos_right_btn}
        if mode in btn:
            btn[mode].setChecked(True)
