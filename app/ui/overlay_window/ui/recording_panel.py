from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from app.ui.shared.vu_meter import VUMeter

class RecordingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        self.record_button = QPushButton("Grabar", self)
        self.record_button.setToolTip("Iniciar/detener grabación de audio\nAtajo: AltGr + G")
        self.send_button = QPushButton("Enviar a LLM", self)
        self.send_button.setObjectName("sendButton")
        self.send_button.setToolTip("Enviar transcripción al modelo de IA\nAtajo: AltGr + \\")
        self.refresh_button = QPushButton("Actualizar dispositivos", self)
        self.refresh_button.setToolTip("Volver a detectar micrófonos y salidas de audio")
        
        self.vu_meter = VUMeter(self, height=16)
        self.vu_meter.setToolTip("Nivel de audio del micrófono")
        
        self.layout.addWidget(self.record_button)
        self.layout.addWidget(self.vu_meter, 1)
        self.layout.addWidget(self.send_button)
        self.layout.addWidget(self.refresh_button)
