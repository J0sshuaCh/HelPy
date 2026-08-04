"""
Indicador persistente de grabación: chip con punto pulsante en el header.
"""
import math
from PyQt5.QtWidgets import QWidget, QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor
from app.ui.shared.hotkeys_display import get_hotkey_display


class PulseDot(QWidget):
    """Punto que pulsa (halo + núcleo) mientras está activo."""

    def __init__(self, parent=None, size=8, color="#EF4444", idle_color="#94A3B8"):
        super().__init__(parent)
        self._active = False
        self._phase = 0
        self._color = QColor(color)
        self._idle_color = QColor(idle_color)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_active(self, active: bool):
        self._active = bool(active)
        if self._active:
            if not self._timer.isActive():
                self._phase = 0
                self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def set_theme(self, active_color: QColor, idle_color: QColor):
        self._color = QColor(active_color)
        self._idle_color = QColor(idle_color)
        self.update()

    def _tick(self):
        self._phase = (self._phase + 1) % 30
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self.rect().center()
        base = self.width() / 2.0 - 1
        painter.setPen(Qt.NoPen)

        if self._active:
            p = (math.sin(2 * math.pi * self._phase / 30.0) + 1.0) / 2.0
            halo = QColor(self._color)
            halo.setAlpha(int(40 + 120 * p))
            painter.setBrush(halo)
            painter.drawEllipse(center, base + 1 + 2.5 * p, base + 1 + 2.5 * p)
            painter.setBrush(self._color)
        else:
            painter.setBrush(self._idle_color)

        painter.drawEllipse(center, base, base)
        painter.end()


class RecordingIndicator(QFrame):
    """Chip de estado siempre visible en el header: '● Listo' / '● Grabando'."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("recordingChip")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        self.dot = PulseDot(self, size=8)
        self.label = QLabel("Listo", self)
        self.label.setObjectName("recordingLabel")

        layout.addWidget(self.dot)
        layout.addWidget(self.label)

        self.set_recording(False)
        self.refresh_hotkey_tooltips()

    def refresh_hotkey_tooltips(self):
        """Actualiza el tooltip con la hotkey actual para que no mienta tras remapear."""
        record_display = get_hotkey_display("toggle_record")
        self.setToolTip(
            "Estado de grabación" + (f"\nAtajo: {record_display}" if record_display else "")
        )

    def set_recording(self, active: bool):
        self.dot.set_active(active)
        self.label.setText("Grabando" if active else "Listo")
        for widget in (self, self.label):
            widget.setProperty("recording", bool(active))
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self.update()

    def set_theme(self, active_color: QColor, idle_color: QColor):
        self.dot.set_theme(active_color, idle_color)
