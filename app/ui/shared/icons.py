import os
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPainter, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtSvg import QSvgRenderer
from app.utils.path_utils import asset_path

_icon_color = "#ffffff"
_icon_cache: dict = {}

def set_icon_color(color: str):
    global _icon_color, _icon_cache
    _icon_color = color
    _icon_cache.clear()

def get_icon(name: str) -> QIcon:
    cache_key = (name, _icon_color)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    path = asset_path(os.path.join("icons", f"{name}.svg"))
    if not os.path.exists(path):
        icon = QIcon()
    else:
        with open(path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        colored_svg = svg_content.replace('stroke="#ffffff"', f'stroke="{_icon_color}"')
        renderer = QSvgRenderer(colored_svg.encode('utf-8'))
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon = QIcon(pixmap)

    _icon_cache[cache_key] = icon
    return icon

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


def render_svg_pixmap(name: str, width: int, height: int) -> QPixmap:
    """Renderiza un SVG de la carpeta icons a un QPixmap del tamaño dado."""
    path = asset_path(os.path.join("icons", f"{name}.svg"))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)
    if not os.path.exists(path):
        return pixmap
    renderer = QSvgRenderer(path)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def get_logo_pixmap(width: int, height: int) -> QPixmap:
    """Retorna el logo HelPy como QPixmap, eligiendo variante según tema."""
    from app.ui.shared.settings import ui_settings as _uis
    tema = _uis.get("tema", "")
    if "(Claro)" in tema:
        name = "HelpyLogoNegro"
    else:
        name = "HelpyLogoBlanco"
    path = asset_path(os.path.join("icons", f"{name}.png"))
    src = QPixmap(path)
    if src.isNull():
        return QPixmap(width, height)
    scaled = src.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    result = QPixmap(scaled.size())
    result.fill(Qt.transparent)
    p = QPainter(result)
    p.drawPixmap(0, 0, scaled)
    p.end()
    return result


def get_color_logo_icon(size: int = 64) -> QIcon:
    """Retorna QIcon del logo a color Helpylogo.png para taskbar/tray."""
    path = asset_path(os.path.join("icons", "Helpylogo.png"))
    src = QPixmap(path)
    if src.isNull():
        return QIcon()
    scaled = src.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    result = QPixmap(scaled.size())
    result.fill(Qt.transparent)
    p = QPainter(result)
    p.drawPixmap(0, 0, scaled)
    p.end()
    return QIcon(result)
