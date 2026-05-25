import sys
import ctypes
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QScreen, QIcon, QPixmap, QColor
from app.core.assistant_controller import AssistantController


class OverlayWindow(QWidget):
    text_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.tray_icon = None
        self.recording = False
        self.assistant = AssistantController()
        self.assistant.on_result(self._on_transcription_result)
        self.assistant.on_status(self._on_status_change)

        self.text_received.connect(self._set_text_safe)
        self.status_changed.connect(self._set_status_safe)

        self.initUI()
        self.init_tray_icon()

    def initUI(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("AYUDIN - Presiona Ctrl+Shift+R para grabar", self)
        self.label.setStyleSheet("""
            color: white;
            font-size: 14px;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 10px 15px;
            border-radius: 8px;
        """)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.setLayout(layout)

        screen = QApplication.primaryScreen().availableGeometry()
        w, h = 420, 100
        x = screen.width() - w - 20
        y = 60
        self.setGeometry(QRect(x, y, w, h))

        self.show()

        if sys.platform == 'win32':
            user32 = ctypes.windll.user32
            WDA_EXCLUDEFROMCAPTURE = 0x00000011
            hwnd = int(self.winId())
            result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if not result:
                print("No se pudo aplicar la propiedad de exclusión de captura.")

    def init_tray_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 120, 215))
        icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(icon, self)

        menu = QMenu()
        self.record_action = menu.addAction("Iniciar grabación")
        self.record_action.triggered.connect(self.toggle_recording)
        menu.addSeparator()
        quit_action = menu.addAction("Salir")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.recording = True
        self.record_action.setText("Detener grabación")
        self.record_action.setIcon(QIcon())
        self.assistant.start_recording()

    def stop_recording(self):
        self.recording = False
        self.record_action.setText("Iniciar grabación")
        self.assistant.stop_recording_and_transcribe()

    def _on_transcription_result(self, text: str):
        self.text_received.emit(text)

    def _on_status_change(self, msg: str):
        self.status_changed.emit(msg)

    def _set_text_safe(self, text: str):
        self.label.setText(text)

    def _set_status_safe(self, msg: str):
        self.label.setText(msg)

    def set_text(self, text):
        self.label.setText(text)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Space and event.modifiers() & Qt.ControlModifier:
            self.toggle_recording()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.assistant.cleanup()
        self.tray_icon.hide()
        QApplication.quit()

    def quit_app(self):
        self.assistant.cleanup()
        self.tray_icon.hide()
        QApplication.quit()

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
    window = OverlayWindow()
    sys.exit(app.exec_())
