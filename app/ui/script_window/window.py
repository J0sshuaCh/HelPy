import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QStackedWidget,
    QFileDialog, QGraphicsOpacityEffect, QApplication
)
from PyQt5.QtCore import Qt

from app.ui.shared import (
    ui_settings, DragMixin, apply_capture_affinity, update_window_position, 
    get_icon
)
from app.ui.shared.animations import AnimatedCollapseMixin
from app.ui.themes import obtener_qss

from .ui import HeaderBar, Toolbar, TextViewer, PdfViewer
from .file_loader import FileLoader
from .zoom import ZoomManager

class ScriptWindow(AnimatedCollapseMixin, DragMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_collapsed = bool(ui_settings.get("script_collapsed", False))
        self.capture_visible = bool(ui_settings.get("script_capture_visible", False))
        self._last_script_path = ui_settings.get("script_path")
        self._opacity = float(ui_settings.get("script_opacity", 0.85))
        self.tema_actual = ui_settings.get("tema", "Slate Minimalist (Clasico)")
        
        self.zoom_manager = ZoomManager(self, float(ui_settings.get("script_zoom", 1.0)))
        self.file_loader = FileLoader(self)

        self._init_ui()
        self._apply_settings()

    def cambiar_tema_interfaz(self, nombre_tema):
        self.tema_actual = nombre_tema
        self._apply_styles()
        self._update_capture_button()
        icon_name = "expand" if self.is_collapsed else "collapse"
        self.edge_button.setIcon(get_icon(icon_name))

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAcceptDrops(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(6)

        HeaderBar.setup(outer, self)

        self.container = QFrame(self)
        self.container.setObjectName("overlayContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        container_layout.setSpacing(10)

        title_row = QHBoxLayout()
        self.title_label = QLabel("Guion (MD/PDF/TXT)", self)
        self.title_label.setObjectName("sectionLabel")
        title_row.addWidget(self.title_label)
        title_row.addStretch(1)
        container_layout.addLayout(title_row)

        Toolbar.setup(container_layout, self, self._opacity)

        self.path_label = QLabel("Arrastra un archivo aqui o usa Abrir", self)
        self.path_label.setObjectName("statusLabel")
        container_layout.addWidget(self.path_label)

        self.viewer_stack = QStackedWidget(self)
        self.md_view = TextViewer(self)
        self.pdf_scroll = PdfViewer(self)

        self.viewer_stack.addWidget(self.md_view)
        self.viewer_stack.addWidget(self.pdf_scroll)
        container_layout.addWidget(self.viewer_stack)

        outer.addWidget(self.container)

        self._setup_collapse_animation(self.container, self.edge_button, duration=300)

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
        self._animate_toggle_collapsed()
        self.edge_button.setToolTip("Expandir" if self.is_collapsed else "Retractar")
        ui_settings.set("script_collapsed", self.is_collapsed)

    def toggle_capture_visibility(self):
        self.capture_visible = not self.capture_visible
        ui_settings.set("script_capture_visible", self.capture_visible)
        self._apply_capture_affinity()
        self._update_capture_button()

    def _apply_capture_affinity(self):
        apply_capture_affinity(int(self.winId()), self.capture_visible)

    def _update_capture_button(self):
        if self.capture_visible:
            self.capture_button.setIcon(get_icon("eye"))
            self.capture_button.setToolTip("Visible en captura")
        else:
            self.capture_button.setIcon(get_icon("eye_off"))
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
        if path:
            self.file_loader.load_script(path)

    def _on_opacity_slider_changed(self, value):
        self._opacity = value / 100.0
        ui_settings.set("script_opacity", self._opacity)
        self._apply_global_opacity()

    def _apply_global_opacity(self):
        self.setWindowOpacity(self._opacity)
        # Apply specifically to PDF pages if they exist
        for i in range(self.pdf_scroll.pdf_layout.count()):
            widget = self.pdf_scroll.pdf_layout.itemAt(i).widget()
            if widget:
                effect = QGraphicsOpacityEffect(widget)
                effect.setOpacity(1.0)
                widget.setGraphicsEffect(effect)

    def _update_after_load(self, path: str):
        self._last_script_path = path
        ui_settings.set("script_path", path)
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
        if urls:
            self.file_loader.load_script(urls[0].toLocalFile())

    def showEvent(self, event):
        super().showEvent(event)
        self.update_position()
        self._apply_capture_affinity()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.zoom_manager.update_pdf_pages_size()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.zoom_manager.handle_wheel_event(event, ui_settings)
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
            self.edge_button.setIcon(get_icon("expand"))
            self.edge_button.setToolTip("Expandir")
        else:
            self.container.setVisible(True)
            self.edge_button.setIcon(get_icon("collapse"))
            self.edge_button.setToolTip("Retractar")

        if self._last_script_path and os.path.exists(self._last_script_path):
            self.file_loader.load_script(self._last_script_path)

        self.adjustSize()

    def _apply_styles(self):
        self.setStyleSheet(obtener_qss(self.tema_actual))
