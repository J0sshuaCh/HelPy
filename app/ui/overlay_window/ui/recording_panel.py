from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QTimer
from app.ui.shared.vu_meter import VUMeter
from app.ui.shared.hotkeys_display import get_hotkey_display

class RecordingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        self.record_button = QPushButton("Grabar", self)
        self.record_button.setObjectName("recordButton")
        self.record_button.setAccessibleName("Iniciar o detener grabación de audio")
        self.send_button = QPushButton("Enviar a IA", self)
        self.send_button.setAccessibleName("Enviar texto a la inteligencia artificial")
        
        self.vu_meter = VUMeter(self, height=16)
        self.vu_meter.setToolTip("Nivel de audio del micrófono")
        self.vu_meter.setAccessibleName("Vúmetro indicador de nivel de audio")

        self.timer_label = QLabel("0:00", self)
        self.timer_label.setObjectName("statusLabel")
        self.timer_label.setAccessibleName("Tiempo de grabación transcurrido")
        self.timer_label.setVisible(False)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._elapsed = 0
        
        self.layout.addWidget(self.record_button)
        self.layout.addWidget(self.vu_meter, 1)
        self.layout.addWidget(self.timer_label)
        self.layout.addWidget(self.send_button)

        self.refresh_hotkey_tooltips()

    def start_timer(self):
        self._elapsed = 0
        self.timer_label.setText("0:00")
        self.timer_label.setVisible(True)
        self._timer.start()

    def stop_timer(self):
        self._timer.stop()
        self.timer_label.setVisible(False)

    def _tick(self):
        self._elapsed += 1
        m, s = divmod(self._elapsed, 60)
        self.timer_label.setText(f"{m:02d}:{s:02d}")

    def refresh_hotkey_tooltips(self):
        """Actualiza los tooltips con las hotkeys actuales para que no mientan tras remapear."""
        record_display = get_hotkey_display("toggle_record")
        send_display = get_hotkey_display("send_llm")
        self.record_button.setToolTip(
            "Iniciar/detener grabación de audio"
            + (f"\nAtajo: {record_display}" if record_display else "")
        )
        self.send_button.setToolTip(
            "Enviar transcripción al modelo de IA"
            + (f"\nAtajo: {send_display}" if send_display else "")
        )

    def set_send_available(self, available: bool):
        """Tooltip contextual del botón de envío según haya o no texto que enviar."""
        if available:
            self.refresh_hotkey_tooltips()
        else:
            self.send_button.setToolTip("Sin transcripción para enviar. Graba algo primero.")
