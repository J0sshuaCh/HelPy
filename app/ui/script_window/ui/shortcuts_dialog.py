from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from app.ui.shared import get_icon, DragMixin
from app.ui.shared.icons import get_logo_pixmap
from app.ui.themes import obtener_qss, normalizar_tema

SHORTCUTS = [
    ("Ctrl + O", "Abrir archivo"),
    ("Ctrl + F", "Buscar en el documento"),
    ("Shift + Enter", "Resultado anterior (búsqueda)"),
    ("Ctrl + P", "Mostrar / ocultar controles"),
    ("Ctrl + H", "Colapsar / expandir"),
    ("Ctrl + Shift + C", "Captura"),
    ("Ctrl + 0", "Restablecer zoom"),
    ("Espacio", "Reproducir / pausar autoscroll"),
    ("↑ / ↓", "Velocidad del autoscroll"),
    ("Ctrl + Rueda", "Zoom"),
    ("Escape", "Cerrar búsqueda / ventana"),
]


class ShortcutsDialog(DragMixin, QWidget):
    def __init__(self, tema, parent=None):
        super().__init__(parent)
        self._tema = normalizar_tema(tema)
        self.setWindowTitle("HelPy – Atajos de teclado")
        self.setObjectName("shortcutsDialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(520)

        self.setWindowIcon(QIcon(get_logo_pixmap(64, 64)))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(6, 4, 6, 0)

        logo = QLabel()
        logo.setPixmap(get_logo_pixmap(38, 20))
        logo.setFixedHeight(20)
        header_row.addWidget(logo)

        title = QLabel("Atajos de teclado")
        title.setObjectName("appTitle")
        header_row.addWidget(title)
        header_row.addStretch(1)

        close_btn = QPushButton()
        close_btn.setObjectName("edgeButton")
        close_btn.setIcon(get_icon("close"))
        close_btn.setIconSize(QSize(14, 14))
        close_btn.setToolTip("Cerrar")
        close_btn.clicked.connect(self.close)
        header_row.addWidget(close_btn)
        outer.addLayout(header_row)

        container = QFrame(self)
        container.setObjectName("overlayContainer")
        body = QVBoxLayout(container)
        body.setContentsMargins(16, 12, 16, 16)
        body.setSpacing(2)

        hint = QLabel(
            "Pasa el ratón por el borde superior del panel de guion "
            "para mostrar los controles ocultos."
        )
        hint.setObjectName("statusLabel")
        hint.setWordWrap(True)
        body.addWidget(hint)
        body.addSpacing(8)

        for key, desc in SHORTCUTS:
            row = QHBoxLayout()
            key_label = QLabel(key)
            key_label.setObjectName("hotkeyChip")
            desc_label = QLabel(desc)
            desc_label.setObjectName("statusLabel")
            row.addWidget(key_label)
            row.addWidget(desc_label, 1)
            row.addStretch(1)
            body.addLayout(row)

        outer.addWidget(container)

        self._apply_theme()

    def _apply_theme(self):
        self.setStyleSheet(obtener_qss(self._tema))

    def cambiar_tema_interfaz(self, nombre_tema):
        self._tema = normalizar_tema(nombre_tema)
        self._apply_theme()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
