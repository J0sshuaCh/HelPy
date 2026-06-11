import os
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QFont
from PyQt5.QtCore import Qt
from app.utils.path_utils import asset_path

def get_icon(name: str) -> QIcon:
    """Loads an icon by name from the assets directory."""
    path = asset_path(os.path.join("icons", f"{name}.svg"))
    if os.path.exists(path):
        return QIcon(path)
    return QIcon()

def get_text_icon(text: str, color: QColor) -> QIcon:
    """Generates an icon with the given text and color."""
    size = 16
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(color)
    font = QFont()
    font.setPointSize(8)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)
