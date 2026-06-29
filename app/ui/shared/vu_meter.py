"""
Widget de nivel de audio (VU meter) como barra visual.
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QLinearGradient


class VUMeter(QWidget):
    """Barra visual que muestra el nivel de audio del micrófono."""
    
    level_changed = pyqtSignal(float)
    
    def __init__(self, parent=None, height=16):
        super().__init__(parent)
        self._level = 0.0
        self._peak = 0.0
        self._peak_decay = 0.98
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)
        self.setMinimumWidth(120)
    
    def set_level(self, level: float):
        """Recibe nivel de 0.0 a 1.0."""
        self._level = max(0.0, min(1.0, level))
        if self._level > self._peak:
            self._peak = self._level
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Fondo
        painter.setBrush(QColor(30, 30, 30))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 3, 3)
        
        # Barra de nivel
        if self._level > 0:
            bar_width = int(w * self._level)
            
            # Gradiente de verde a amarillo a rojo
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0.0, QColor(16, 185, 129))    # Verde
            gradient.setColorAt(0.6, QColor(234, 179, 8))     # Amarillo
            gradient.setColorAt(0.85, QColor(239, 68, 68))    # Rojo
            gradient.setColorAt(1.0, QColor(239, 68, 68))     # Rojo
            
            painter.setBrush(gradient)
            painter.drawRoundedRect(1, 1, bar_width - 2, h - 2, 2, 2)
        
        # Pico (peak)
        if self._peak > 0.01:
            peak_x = int(w * self._peak)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRect(peak_x - 1, 2, 2, h - 4)
        
        # Decaimiento del pico
        self._peak *= self._peak_decay
        if self._peak < self._level:
            self._peak = self._level
        
        painter.end()
