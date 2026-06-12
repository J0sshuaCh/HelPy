from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PyQt5.QtCore import QSize
from app.ui.shared import get_icon

class CapturePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        self.capture_mode_group = QButtonGroup(self)
        self.capture_mode_group.setExclusive(True)
        
        self.capture_mic_btn = QPushButton("Mic", self)
        self.capture_mic_btn.setObjectName("modeButton")
        self.capture_mic_btn.setCheckable(True)
        self.capture_mic_btn.setIcon(get_icon("mic"))
        self.capture_mic_btn.setIconSize(QSize(16, 16))
        self.capture_mic_btn.setToolTip("Solo microfono")
        
        self.capture_sys_btn = QPushButton("Equipo", self)
        self.capture_sys_btn.setObjectName("modeButton")
        self.capture_sys_btn.setCheckable(True)
        self.capture_sys_btn.setIcon(get_icon("monitor"))
        self.capture_sys_btn.setIconSize(QSize(16, 16))
        self.capture_sys_btn.setToolTip("Solo audio del equipo")
        
        self.capture_both_btn = QPushButton("Ambos", self)
        self.capture_both_btn.setObjectName("modeButton")
        self.capture_both_btn.setCheckable(True)
        self.capture_both_btn.setIcon(get_icon("mic_monitor"))
        self.capture_both_btn.setIconSize(QSize(16, 16))
        self.capture_both_btn.setToolTip("Microfono y sistema")

        
        self.capture_mode_group.addButton(self.capture_mic_btn)
        self.capture_mode_group.addButton(self.capture_sys_btn)
        self.capture_mode_group.addButton(self.capture_both_btn)
        
        self.layout.addWidget(self.capture_mic_btn, 1)
        self.layout.addWidget(self.capture_sys_btn, 1)
        self.layout.addWidget(self.capture_both_btn, 1)

    def reload_icons(self):
        self.capture_mic_btn.setIcon(get_icon("mic"))
        self.capture_sys_btn.setIcon(get_icon("monitor"))
        self.capture_both_btn.setIcon(get_icon("mic_monitor"))
