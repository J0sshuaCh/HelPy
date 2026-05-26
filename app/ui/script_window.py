import sys
import ctypes
import json
import os

from PyQt5.QtWidgets import (
    QWidget,
    QApplication,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QFrame,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon


class ScriptWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = self._load_settings()
        self.is_collapsed = bool(self.settings.get("script_collapsed", False))
        self.capture_visible = bool(self.settings.get("script_capture_visible", False))
        self._last_markdown_path = self.settings.get("script_markdown_path")

        self._init_ui()
        self._apply_settings()

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # Drag & drop for .md
        self.setAcceptDrops(True)

        outer = QVBoxLayout()
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addStretch(1)

        self.capture_button = QPushButton(self)
        self.capture_button.setObjectName("edgeButton")
        self.capture_button.setIconSize(QSize(14, 14))
        self.capture_button.setText("")
        self.capture_button.clicked.connect(self.toggle_capture_visibility)

        self.edge_button = QPushButton(self)
        self.edge_button.setObjectName("edgeButton")
        self.edge_button.setIconSize(QSize(14, 14))
        self.edge_button.setText("")
        self.edge_button.clicked.connect(self.toggle_collapsed)

        header_row.addWidget(self.capture_button, 0)
        header_row.addWidget(self.edge_button, 0)
        outer.addLayout(header_row)

        self.container = QFrame(self)
        self.container.setObjectName("overlayContainer")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(10)
        self.container.setLayout(container_layout)

        title = QLabel("Guion (Markdown)", self)
        title.setObjectName("sectionLabel")
        container_layout.addWidget(title)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.open_button = QPushButton("Abrir .md", self)
        self.open_button.clicked.connect(self.open_markdown_file)
        button_row.addWidget(self.open_button)
        button_row.addStretch(1)
        container_layout.addLayout(button_row)

        self.path_label = QLabel("", self)
        self.path_label.setObjectName("statusLabel")
        self.path_label.setText("Arrastra un .md aqui o usa Abrir .md")
        container_layout.addWidget(self.path_label)

        self.md_view = QTextEdit(self)
        self.md_view.setReadOnly(True)
        self.md_view.setObjectName("textArea")
        self.md_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.md_view.setAcceptRichText(True)
        container_layout.addWidget(self.md_view)

        outer.addWidget(self.container)
        self.setLayout(outer)

        self._apply_styles()
        self._apply_window_size()

        self.show()
        self.adjustSize()
        self.update_position()

    def _apply_window_size(self):
        screen = QApplication.primaryScreen().availableGeometry()
        max_width = int(screen.width() * 0.46)
        width = min(640, max_width)
        self.setFixedWidth(width)

        # Viewer height: keep window compact but usable.
        min_h = int(screen.height() * 0.25)
        max_h = int(screen.height() * 0.60)
        self.md_view.setMinimumHeight(max(180, min_h))
        self.md_view.setMaximumHeight(max(260, max_h))

        self.adjustSize()

    def update_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        w = self.width()
        margin = 20
        x = int((screen.width() - w) / 2)
        self.move(x, margin)

    def toggle_collapsed(self):
        self.is_collapsed = not self.is_collapsed
        self.container.setVisible(not self.is_collapsed)
        if self.is_collapsed:
            self.edge_button.setIcon(self._icon("expand"))
            self.edge_button.setToolTip("Expandir")
        else:
            self.edge_button.setIcon(self._icon("collapse"))
            self.edge_button.setToolTip("Retractar")
        self.settings["script_collapsed"] = self.is_collapsed
        self._save_settings()
        self.adjustSize()
        self.update_position()

    def toggle_capture_visibility(self):
        self.capture_visible = not self.capture_visible
        self.settings["script_capture_visible"] = self.capture_visible
        self._save_settings()
        self._apply_capture_affinity()
        self._update_capture_button()

    def _apply_capture_affinity(self):
        if sys.platform != "win32":
            return
        user32 = ctypes.windll.user32
        WDA_NONE = 0x00000000
        WDA_EXCLUDEFROMCAPTURE = 0x00000011
        hwnd = int(self.winId())
        affinity = WDA_NONE if self.capture_visible else WDA_EXCLUDEFROMCAPTURE
        user32.SetWindowDisplayAffinity(hwnd, affinity)

    def _update_capture_button(self):
        if self.capture_visible:
            self.capture_button.setIcon(self._icon("eye"))
            self.capture_button.setToolTip("Visible en captura")
        else:
            self.capture_button.setIcon(self._icon("eye_off"))
            self.capture_button.setToolTip("Oculto en captura")

    def open_markdown_file(self):
        start_dir = ""
        if self._last_markdown_path and os.path.exists(self._last_markdown_path):
            start_dir = os.path.dirname(self._last_markdown_path)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Markdown",
            start_dir,
            "Markdown (*.md *.markdown);;Todos (*.*)",
        )
        if not path:
            return
        self.load_markdown(path)

    def load_markdown(self, path: str):
        if not path:
            return
        if not os.path.exists(path):
            self.path_label.setText(f"No existe: {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1", errors="replace") as handle:
                text = handle.read()
        except OSError as exc:
            self.path_label.setText(f"Error leyendo: {exc}")
            return

        # Render markdown (PyQt5 provides QTextEdit.setMarkdown).
        self.md_view.setMarkdown(text)
        self._last_markdown_path = path
        self.settings["script_markdown_path"] = path
        self._save_settings()
        self.path_label.setText(path)

        # Scroll to top by default for a script.
        self.md_view.verticalScrollBar().setValue(0)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                p = urls[0].toLocalFile()
                if p.lower().endswith((".md", ".markdown")):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if path.lower().endswith((".md", ".markdown")):
            self.load_markdown(path)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_position()
        self._apply_capture_affinity()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_position()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        if event.key() == Qt.Key_O and event.modifiers() & Qt.ControlModifier:
            self.open_markdown_file()
            return
        super().keyPressEvent(event)

    def _apply_settings(self):
        self._update_capture_button()
        self._apply_capture_affinity()

        if self.is_collapsed:
            self.container.setVisible(False)
            self.edge_button.setIcon(self._icon("expand"))
            self.edge_button.setToolTip("Expandir")
        else:
            self.container.setVisible(True)
            self.edge_button.setIcon(self._icon("collapse"))
            self.edge_button.setToolTip("Retractar")

        if self._last_markdown_path and os.path.exists(self._last_markdown_path):
            self.load_markdown(self._last_markdown_path)

        self.adjustSize()
        self.update_position()

    def _apply_styles(self):
        # Same visual language as overlay_window.py, slightly transparent.
        self.setStyleSheet(
            """
            QWidget {
                font-family: "Cascadia Mono", "Consolas", "Lucida Console", "Courier New", monospace;
            }
            #overlayContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 40, 62, 190), stop:1 rgba(16, 24, 38, 190));
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 16px;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 12px;
            }
            #statusLabel {
                color: #b8c0cc;
                font-size: 11px;
            }
            #sectionLabel {
                font-size: 11px;
                color: #cbd5e1;
                padding-left: 4px;
            }
            #edgeButton {
                background-color: rgba(26, 36, 54, 190);
                color: #e5e7eb;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 11px;
                min-height: 22px;
            }
            QPushButton {
                background-color: rgba(28, 40, 62, 190);
                color: #e5e7eb;
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(38, 54, 82, 210);
            }
            QTextEdit#textArea {
                background-color: rgba(14, 20, 34, 190);
                color: #e5e7eb;
                border: 1px solid rgba(255, 255, 255, 35);
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(10, 15, 25, 100);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 50);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 80);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            """
        )

    def _config_path(self):
        base = os.path.join(os.path.dirname(__file__), "..", "config")
        return os.path.abspath(os.path.join(base, "ui_settings.json"))

    def _load_settings(self):
        path = self._config_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_settings(self):
        path = self._config_path()
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.settings, handle, indent=2)
        except OSError:
            pass

    def _icon(self, name: str) -> QIcon:
        path = self._asset_path(os.path.join("icons", f"{name}.svg"))
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()

    def _asset_path(self, relative: str) -> str:
        base = os.path.join(os.path.dirname(__file__), "..", "assets")
        return os.path.abspath(os.path.join(base, relative))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScriptWindow()
    sys.exit(app.exec_())
