from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen
from app.ui.themes import PALETAS as _TEMA_PALETAS

_DEFAULT_TEMA = _TEMA_PALETAS["Slate Minimalist (Clásico)"]


class LoadingSpinner(QWidget):
    def __init__(self, parent=None, size=16, line_width=2, speed=40, color=None):
        super().__init__(parent)
        self._angle = 0
        self._line_width = line_width
        self._speed = speed
        self._color = color or QColor(_DEFAULT_TEMA["resaltado"])
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._spinning = False

        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

    def set_color(self, color: QColor):
        self._color = color
        self.update()

    def set_line_width(self, width: int):
        self._line_width = width
        self.update()

    def paintEvent(self, event):
        if not self._spinning:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        pen = QPen(self._color, self._line_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)

        margin = self._line_width
        draw_rect = QRectF(rect).adjusted(margin, margin, -margin, -margin)
        span = 300
        start = self._angle * 16
        painter.drawArc(draw_rect, start, span * 16)

        painter.end()

    def _rotate(self):
        self._angle = (self._angle + 30) % 360
        self.update()

    def start(self):
        self._spinning = True
        self.show()
        self._timer.start(self._speed)

    def stop(self):
        self._spinning = False
        self._timer.stop()
        self.hide()
        self.update()

    def is_spinning(self) -> bool:
        return self._spinning


class SpinnerOverlay(QFrame):
    def __init__(self, parent=None, spinner_size=48, color=None):
        super().__init__(parent)
        self.setObjectName("spinnerOverlay")
        # El overlay es solo señal visual: nunca debe bloquear la interacción con el panel
        # (p. ej. poder pulsar "Cancelar envío" mientras la IA trabaja).
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._scrim = _DEFAULT_TEMA["scrim"]
        self._label_color = QColor(_DEFAULT_TEMA["texto"])
        self._apply_styles()
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self.spinner = LoadingSpinner(self, size=spinner_size, line_width=4, speed=40, color=color)
        layout.addWidget(self.spinner, 0, Qt.AlignCenter)

        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "color: %s; font-size: 14px; background: transparent;" % self._label_color.name())
        self.label.hide()
        layout.addWidget(self.label, 0, Qt.AlignCenter)

    def _apply_styles(self):
        self.setStyleSheet(
            "background-color: %s; border-radius: 8px;" % self._scrim)

    def set_theme(self, scrim, label_color):
        self._scrim = scrim
        self._label_color = QColor(label_color)
        self._apply_styles()
        self.label.setStyleSheet(
            "color: %s; font-size: 14px; background: transparent;" % self._label_color.name())
        self.update()

    def show_overlay(self, text=""):
        parent = self.parent()
        if parent:
            self.setGeometry(parent.rect())
        self.raise_()
        if text:
            self.label.setText(text)
            self.label.show()
        else:
            self.label.hide()
        self.spinner.start()
        self.show()

    def hide_overlay(self):
        self.spinner.stop()
        self.hide()

    def set_text(self, text: str):
        self.label.setText(text)
        self.label.setVisible(bool(text))

    def resizeEvent(self, event):
        parent = self.parent()
        if parent:
            self.setGeometry(parent.rect())
        super().resizeEvent(event)
