import sys
import ctypes
import json
import os
import fitz  # PyMuPDF

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
    QScrollArea,
    QStackedWidget,
    QSlider,
    QGraphicsOpacityEffect,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QImage, QPixmap


class ScriptWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings = self._load_settings()
        self.is_collapsed = bool(self.settings.get("script_collapsed", False))
        self.capture_visible = bool(self.settings.get("script_capture_visible", False))
        self._last_script_path = self.settings.get("script_path")
        self._zoom_factor = float(self.settings.get("script_zoom", 1.0))
        self._opacity = float(self.settings.get("script_opacity", 0.85))
        
        # Dragging support
        self._drag_pos = None

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

        title_row = QHBoxLayout()
        self.title_label = QLabel("Guion (MD/PDF/TXT)", self)
        self.title_label.setObjectName("sectionLabel")
        title_row.addWidget(self.title_label)
        title_row.addStretch(1)
        container_layout.addLayout(title_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.open_button = QPushButton("Abrir Archivo", self)
        self.open_button.clicked.connect(self.open_script_file)
        button_row.addWidget(self.open_button)
        
        button_row.addStretch(1)

        opacity_label = QLabel("Opacidad:", self)
        opacity_label.setObjectName("statusLabel")
        button_row.addWidget(opacity_label)

        self.opacity_slider = QSlider(Qt.Horizontal, self)
        self.opacity_slider.setMinimum(20)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(int(self._opacity * 100))
        self.opacity_slider.setFixedWidth(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity_slider_changed)
        button_row.addWidget(self.opacity_slider)

        container_layout.addLayout(button_row)

        self.path_label = QLabel("", self)
        self.path_label.setObjectName("statusLabel")
        self.path_label.setText("Arrastra un archivo aqui o usa Abrir")
        container_layout.addWidget(self.path_label)

        # Viewer Stack: Switch between Text and PDF
        self.viewer_stack = QStackedWidget(self)
        
        # Text/Markdown Viewer
        self.md_view = QTextEdit(self)
        self.md_view.setReadOnly(True)
        self.md_view.setObjectName("textArea")
        self.md_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # PDF Viewer (Scroll Area with Image Labels)
        self.pdf_scroll = QScrollArea(self)
        self.pdf_scroll.setWidgetResizable(True)
        self.pdf_scroll.setObjectName("pdfScroll")
        self.pdf_scroll.setStyleSheet("background: transparent; border: none;")
        self.pdf_container = QWidget()
        self.pdf_container.setObjectName("pdfContainer")
        self.pdf_container.setStyleSheet("background: transparent;")
        self.pdf_layout = QVBoxLayout(self.pdf_container)
        self.pdf_layout.setContentsMargins(0, 0, 0, 0)
        self.pdf_layout.setSpacing(10)
        self.pdf_layout.setAlignment(Qt.AlignHCenter)
        self.pdf_scroll.setWidget(self.pdf_container)

        self.viewer_stack.addWidget(self.md_view)
        self.viewer_stack.addWidget(self.pdf_scroll)
        
        container_layout.addWidget(self.viewer_stack)

        outer.addWidget(self.container)
        self.setLayout(outer)

        self._apply_styles()
        self._apply_window_size()

        self.show()
        self.adjustSize()
        self.update_position()
        self._apply_global_opacity()

    def _apply_window_size(self):
        screen = QApplication.primaryScreen().availableGeometry()
        max_width = int(screen.width() * 0.46)
        width = min(640, max_width)
        self.setFixedWidth(width)

        # Viewer height: keep window compact but usable.
        min_h = int(screen.height() * 0.25)
        max_h = int(screen.height() * 0.60)
        h_val = max(180, min_h)
        self.md_view.setMinimumHeight(h_val)
        self.md_view.setMaximumHeight(max(260, max_h))
        self.pdf_scroll.setMinimumHeight(h_val)
        self.pdf_scroll.setMaximumHeight(max(260, max_h))

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
        # Removed update_position() here to preserve user-set position

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

    def open_script_file(self):
        start_dir = ""
        if self._last_script_path and os.path.exists(self._last_script_path):
            start_dir = os.path.dirname(self._last_script_path)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Guion",
            start_dir,
            "Documentos (*.md *.markdown *.pdf *.txt);;Todos (*.*)",
        )
        if not path:
            return
        self.load_script(path)

    def load_script(self, path: str):
        if not path:
            return
        if not os.path.exists(path):
            self.path_label.setText(f"No existe: {path}")
            return

        ext = path.lower()
        if ext.endswith((".md", ".markdown")):
            self.load_markdown(path)
        elif ext.endswith(".pdf"):
            self.load_pdf(path)
        elif ext.endswith(".txt"):
            self.load_txt(path)
        else:
            self.path_label.setText(f"Formato no soportado: {path}")

    def _on_opacity_slider_changed(self, value):
        self._opacity = value / 100.0
        self.settings["script_opacity"] = self._opacity
        self._save_settings()
        self._apply_global_opacity()

    def _apply_global_opacity(self):
        # 1. Apply to the whole window
        self.setWindowOpacity(self._opacity)
        
        # 2. Apply specifically to PDF pages if they exist
        for i in range(self.pdf_layout.count()):
            widget = self.pdf_layout.itemAt(i).widget()
            if widget:
                # We use a graphics effect for the content to ensure it blends well
                # though setWindowOpacity already does most of the work, 
                # this ensures the labels themselves don't have opaque backgrounds.
                effect = QGraphicsOpacityEffect(widget)
                effect.setOpacity(1.0) # Window opacity handles the rest
                widget.setGraphicsEffect(effect)

    def load_pdf(self, path: str):
        try:
            self._clear_pdf_layout()
            doc = fitz.open(path)
            
            # Use high DPI for base images
            zoom = 2.0 
            mat = fitz.Matrix(zoom, zoom)

            for page in doc:
                pix = page.get_pixmap(matrix=mat, alpha=False)
                fmt = QImage.Format_RGB888
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                
                label = QLabel()
                pixmap = QPixmap.fromImage(img)
                label.setPixmap(pixmap)
                # Store the original pixmap for resizing
                label.setProperty("original_pixmap", pixmap)
                label.setAlignment(Qt.AlignCenter)
                
                # Apply initial opacity effect container
                effect = QGraphicsOpacityEffect(label)
                effect.setOpacity(1.0) # Controlled by window opacity
                label.setGraphicsEffect(effect)
                
                self.pdf_layout.addWidget(label)
            
            doc.close()
            self._last_script_path = path
            self.viewer_stack.setCurrentWidget(self.pdf_scroll)
            self._update_pdf_pages_size()
            self._update_after_load(path)
        except Exception as exc:
            self.path_label.setText(f"Error PDF: {exc}")

    def _clear_pdf_layout(self):
        for i in reversed(range(self.pdf_layout.count())): 
            widget = self.pdf_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def _update_pdf_pages_size(self):
        if self.viewer_stack.currentWidget() != self.pdf_scroll:
            return
            
            # Target width: container width minus scrollbar and margins
        target_width = int((self.container.width() - 45) * self._zoom_factor)
        
        for i in range(self.pdf_layout.count()):
            label = self.pdf_layout.itemAt(i).widget()
            if isinstance(label, QLabel):
                orig = label.property("original_pixmap")
                if orig:
                    scaled = orig.scaledToWidth(target_width, Qt.SmoothTransformation)
                    label.setPixmap(scaled)
                    
                # Re-apply effect after scaling if needed
                if not label.graphicsEffect():
                    effect = QGraphicsOpacityEffect(label)
                    effect.setOpacity(1.0)
                    label.setGraphicsEffect(effect)

    def load_txt(self, path: str):
        text = self._read_text_file(path)
        if text is not None:
            self.md_view.setPlainText(text)
            self._apply_text_zoom()
            self.viewer_stack.setCurrentWidget(self.md_view)
            self._update_after_load(path)

    def load_markdown(self, path: str):
        text = self._read_text_file(path)
        if text is not None:
            self.md_view.setMarkdown(text)
            self._apply_text_zoom()
            self.viewer_stack.setCurrentWidget(self.md_view)
            self._update_after_load(path)

    def _apply_text_zoom(self):
        # Base size is 13px, apply zoom factor
        new_size = max(8, int(13 * self._zoom_factor))
        font = self.md_view.font()
        font.setPointSize(new_size)
        self.md_view.setFont(font)

    def _read_text_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return handle.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1", errors="replace") as handle:
                    return handle.read()
            except Exception as exc:
                self.path_label.setText(f"Error leyendo: {exc}")
                return None
        except OSError as exc:
            self.path_label.setText(f"Error OSError: {exc}")
            return None

    def _update_after_load(self, path: str):
        self._last_script_path = path
        self.settings["script_path"] = path
        self._save_settings()
        self.path_label.setText(path)
        
        # Scroll to top
        if self.viewer_stack.currentWidget() == self.md_view:
            self.md_view.verticalScrollBar().setValue(0)
        else:
            self.pdf_scroll.verticalScrollBar().setValue(0)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                p = urls[0].toLocalFile()
                if p.lower().endswith((".md", ".markdown", ".pdf", ".txt")):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        self.load_script(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().y() < 80:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_position()
        self._apply_capture_affinity()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Removed update_position() here to preserve user-set position
        self._update_pdf_pages_size()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_factor = min(3.0, self._zoom_factor + 0.1)
            else:
                self._zoom_factor = max(0.5, self._zoom_factor - 0.1)
            
            self.settings["script_zoom"] = self._zoom_factor
            self._save_settings()
            
            if self.viewer_stack.currentWidget() == self.pdf_scroll:
                self._update_pdf_pages_size()
            else:
                self._apply_text_zoom()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        if event.key() == Qt.Key_O and event.modifiers() & Qt.ControlModifier:
            self.open_script_file()
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

        if self._last_script_path and os.path.exists(self._last_script_path):
            self.load_script(self._last_script_path)

        self.adjustSize()
        # Removed update_position() here to preserve user-set position

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                font-family: "Inter", "Roboto", "Segoe UI", "Arial", sans-serif;
            }
            #overlayContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 40, 62, 190), stop:1 rgba(16, 24, 38, 190));
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 8px;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 12px;
            }
            #statusLabel {
                color: #94a3b8;
                font-size: 11px;
            }
            #sectionLabel {
                font-size: 13px;
                font-weight: bold;
                color: #F3F4F6;
                padding-left: 4px;
            }
            #edgeButton {
                background-color: rgba(26, 36, 54, 190);
                color: #e5e7eb;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 11px;
                min-height: 22px;
            }
            #edgeButton:hover {
                background-color: rgba(96, 165, 250, 220);
                border-color: rgba(255, 255, 255, 80);
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
                background-color: rgba(96, 165, 250, 220);
                border-color: rgba(255, 255, 255, 80);
            }
            QTextEdit#textArea {
                background-color: rgba(20, 32, 52, 220);
                color: #e5e7eb;
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
                padding: 15px;
                font-size: 13px;
                line-height: 150%;
            }
            #pdfScroll {
                background-color: rgba(20, 32, 52, 220);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 8px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: rgba(14, 20, 34, 150);
                width: 10px;
                height: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 40);
                min-height: 30px;
                min-width: 30px;
                border-radius: 5px;
                border: 1px solid rgba(255, 255, 255, 20);
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 70);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                height: 0px;
                width: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QSlider::handle:horizontal {
                background: #60a5fa;
                border: 1px solid rgba(255, 255, 255, 50);
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::groove:horizontal {
                border: 1px solid rgba(255, 255, 255, 30);
                height: 4px;
                background: rgba(0, 0, 0, 100);
                margin: 2px 0;
                border-radius: 2px;
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
