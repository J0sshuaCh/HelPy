from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton

class RecordingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        self.record_button = QPushButton("Grabar", self)
        self.send_button = QPushButton("Enviar a LLM", self)
        self.send_button.setObjectName("sendButton")
        self.refresh_button = QPushButton("Actualizar dispositivos", self)
        
        self.layout.addWidget(self.record_button)
        self.layout.addWidget(self.send_button)
        self.layout.addWidget(self.refresh_button)
