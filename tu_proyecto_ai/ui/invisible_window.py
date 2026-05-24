import sys
import ctypes
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QScreen, QIcon, QPixmap, QColor


class InvisibleWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.tray_icon = None
        self.initUI()
        self.init_tray_icon()

    def initUI(self):
        # Configuración inicial de la ventana transparente
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Crear layout para contenido
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Esperando entrada...", self)
        label.setStyleSheet("""
            color: white;
            font-size: 14px;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 10px 15px;
            border-radius: 8px;
        """)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.setLayout(layout)

        screen = QApplication.primaryScreen().availableGeometry()
        w, h = 420, 100
        x = screen.width() - w - 20
        y = 60
        self.setGeometry(QRect(x, y, w, h))

        self.show()

        # Excluir de captura de pantalla (Windows)
        if sys.platform == 'win32':
            user32 = ctypes.windll.user32
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            hwnd = int(self.winId())
            result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if not result:
                print("No se pudo aplicar la propiedad de exclusión de captura.")
                print("Verifica que Windows 10 Build 19041+ esté instalado.")

    def init_tray_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 120, 215))
        icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(icon, self)

        menu = QMenu()
        quit_action = menu.addAction("Salir")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.tray_icon.hide()
        QApplication.quit()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    def set_text(self, text):
        """Actualizar el texto visible en la ventana"""
        layout = self.layout()
        if layout:
            label = layout.itemAt(0).widget()
            if label and isinstance(label, QLabel):
                label.setText(text)

    def move_to_corner(self, corner="top-right"):
        screen = QApplication.primaryScreen().availableGeometry()
        w = self.width()
        h = self.height()
        margin = 20
        if corner == "top-right":
            self.move(screen.width() - w - margin, margin)
        elif corner == "bottom-right":
            self.move(screen.width() - w - margin, screen.height() - h - margin)
        elif corner == "top-left":
            self.move(margin, margin)
        elif corner == "bottom-left":
            self.move(margin, screen.height() - h - margin)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InvisibleWindow()
    sys.exit(app.exec_())
