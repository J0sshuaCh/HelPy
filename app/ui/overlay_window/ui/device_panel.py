from PyQt5.QtWidgets import QWidget, QHBoxLayout, QComboBox

class DevicePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        self.mic_combo = QComboBox(self)
        self.mic_combo.setObjectName("deviceCombo")
        
        self.sys_combo = QComboBox(self)
        self.sys_combo.setObjectName("deviceCombo")
        
        self.layout.addWidget(self.mic_combo, 1)
        self.layout.addWidget(self.sys_combo, 1)
