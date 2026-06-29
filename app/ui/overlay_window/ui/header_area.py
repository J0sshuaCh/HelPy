from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSlider, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from app.ui.shared import get_icon

class HeaderArea(QFrame):
    def __init__(self, title="HelPy", initial_opacity=100, parent=None):
        super().__init__(parent)
        self.setObjectName("headerArea")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 2)
        self.layout.setSpacing(5)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("appTitle")
        
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(initial_opacity)
        self.opacity_slider.setFixedWidth(100)
        self.opacity_slider.setObjectName("opacitySlider")
        self.opacity_slider.setToolTip("Ajustar opacidad de la ventana (20-100%)")
        
        self.capture_button = QPushButton("", self)
        self.capture_button.setObjectName("edgeButton")
        self.capture_button.setIcon(get_icon("eye_off"))
        self.capture_button.setIconSize(QSize(14, 14))
        self.capture_button.setToolTip("Mostrar/ocultar ventana en capturas de pantalla")
        
        self.compact_button = QPushButton("", self)
        self.compact_button.setObjectName("edgeButton")
        self.compact_button.setIcon(get_icon("expand"))
        self.compact_button.setIconSize(QSize(14, 14))
        self.compact_button.setToolTip("Modo compacto/expandido\nAlterna mostrar todo o solo respuesta")
        
        self.edge_button = QPushButton("", self)
        self.edge_button.setObjectName("edgeButton")
        self.edge_button.setIcon(get_icon("collapse"))
        self.edge_button.setIconSize(QSize(14, 14))
        self.edge_button.setToolTip("Colapsar/expandir panel\nAtajo: AltGr + H")
        
        self.layout.addWidget(self.title_label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.capture_button)
        self.layout.addWidget(self.compact_button)
        self.layout.addWidget(self.edge_button)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(self.sizeHint().height())
