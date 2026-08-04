"""
Widget de nivel de audio (VU meter) como barra visual.
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QLinearGradient
from app.ui.themes import PALETAS as _TEMA_PALETAS

_DEFAULT_TEMA = _TEMA_PALETAS["Slate Minimalist (Clásico)"]


class VUMeter(QWidget):
    """Barra visual que muestra el nivel de audio del micrófono."""
    
    level_changed = pyqtSignal(float)
    
    def __init__(self, parent=None, height=16):
        super().__init__(parent)
        self._level = 0.0
        self._peak = 0.0
        self._peak_decay = 0.98
        self._track = QColor(_DEFAULT_TEMA["vu_track"])
        self._verde = QColor(_DEFAULT_TEMA["vu_verde"])
        self._ambar = QColor(_DEFAULT_TEMA["vu_ambar"])
        self._rojo = QColor(_DEFAULT_TEMA["vu_rojo"])
        self._pico = QColor(_DEFAULT_TEMA["vu_pico"])
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        self.setMinimumWidth(120)
    
    def set_theme(self, track, verde, ambar, rojo, pico):
        """Aplica los colores del tema activo (track, semáforo y pico)."""
        self._track = QColor(track)
        self._verde = QColor(verde)
        self._ambar = QColor(ambar)
        self._rojo = QColor(rojo)
        self._pico = QColor(pico)
        self.update()
    
    def set_level(self, level: float):
        """Recibe nivel de 0.0 a 1.0."""
        self._level = max(0.0, min(1.0, level))
        if self._level > self._peak:
            self._peak = self._level
        self.update()

    def reset(self):
        """Vuelve la barra a nivel y pico en reposo (al detener la grabación)."""
        self._level = 0.0
        self._peak = 0.0
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Fondo
        painter.setBrush(self._track)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 3, 3)
        
        # Barra de nivel
        if self._level > 0:
            bar_width = int(w * self._level)
            
            # Gradiente de verde a amarillo a rojo
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0.0, self._verde)
            gradient.setColorAt(0.6, self._ambar)
            gradient.setColorAt(0.85, self._rojo)
            gradient.setColorAt(1.0, self._rojo)
            
            painter.setBrush(gradient)
            painter.drawRoundedRect(1, 1, bar_width - 2, h - 2, 2, 2)
        
        # Pico (peak)
        if self._peak > 0.01:
            peak_x = int(w * self._peak)
            painter.setBrush(self._pico)
            painter.drawRect(peak_x - 1, 2, 2, h - 4)
        
        # Decaimiento del pico
        self._peak *= self._peak_decay
        if self._peak < self._level:
            self._peak = self._level
        
        painter.end()
