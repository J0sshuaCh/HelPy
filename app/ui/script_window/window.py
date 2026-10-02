import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QStackedWidget,
    QFileDialog, QGraphicsOpacityEffect, QApplication, QPushButton
)
from PyQt5.QtCore import Qt, QTimer, QSize

from app.ui.shared import (
    ui_settings, DragMixin, apply_capture_affinity, update_window_position, 
    get_icon
)
from app.ui.shared.animations import AnimatedCollapseMixin
from app.ui.themes import obtener_qss, normalizar_tema

from .ui import HeaderBar, Toolbar, TextViewer, PdfViewer
from .file_loader import FileLoader
from .zoom import ZoomManager
from .search_bar import SearchBar
from .autoscroll import AutoScrollManager

class ScriptWindow(AnimatedCollapseMixin, DragMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_collapsed = bool(ui_settings.get("script_collapsed", False))
        self.capture_visible = bool(ui_settings.get("script_capture_visible", False))
        self._last_script_path = ui_settings.get("script_path")
        stored = ui_settings.get("script_opacity", 85)
        self._opacity = int(stored * 100) if isinstance(stored, float) else int(stored)
        self.tema_actual = normalizar_tema(ui_settings.get("tema", "Slate Minimalist (Clásico)"))

        from PyQt5.QtGui import QIcon
        from app.ui.shared.icons import get_logo_pixmap
        self.setWindowIcon(QIcon(get_logo_pixmap(64, 64)))
        
        self.zoom_manager = ZoomManager(self, float(ui_settings.get("script_zoom", 1.0)))
        self.file_loader = FileLoader(self)
        self.auto_scroll = AutoScrollManager(self)
        self.auto_scroll.stopped.connect(self._on_autoscroll_stopped)

        self._init_ui()
        self._apply_settings()

    def cambiar_tema_interfaz(self, nombre_tema):
        self.tema_actual = nombre_tema
        self._apply_styles()
        self._update_capture_button()
        self.panel_toggle_button.setIcon(get_icon("panels"))
        self.help_button.setIcon(get_icon("help"))
        self._sync_autoscroll_button()
        self.scroll_slower_btn.setIcon(get_icon("minus"))
        self.scroll_faster_btn.setIcon(get_icon("plus"))
        self.reading_slower_btn.setIcon(get_icon("minus"))
        self.reading_faster_btn.setIcon(get_icon("plus"))
        self.reading_restart_btn.setIcon(get_icon("refresh"))
        icon_name = "expand" if self.is_collapsed else "collapse"
        self.edge_button.setIcon(get_icon(icon_name))
        if hasattr(self, "_shortcuts_dialog") and self._shortcuts_dialog.isVisible():
            self._shortcuts_dialog.cambiar_tema_interfaz(nombre_tema)

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
        container_layout.setContentsMargins(8, 6, 8, 8)
        container_layout.setSpacing(6)

        # --- Panel de control: título + toolbar + autoscroll + ruta ---
        self.control_panel = QFrame(self.container)
        self.control_panel.setObjectName("controlPanel")
        panel_layout = QVBoxLayout(self.control_panel)
        panel_layout.setContentsMargins(0, 0, 0, 4)
        panel_layout.setSpacing(6)

        Toolbar.setup(panel_layout, self, self._opacity)
        Toolbar.setup_autoscroll(panel_layout, self)

        self.scroll_play_btn.setVisible(False)
        self.scroll_slower_btn.setVisible(False)
        self.scroll_faster_btn.setVisible(False)
        self.scroll_speed_label.setVisible(False)
        self.scroll_status_label.setVisible(False)

        self.path_label = QLabel("Arrastra un archivo aquí o usa Abrir", self)
        self.path_label.setObjectName("statusLabel")
        panel_layout.addWidget(self.path_label)

        container_layout.addWidget(self.control_panel)

        # Barra de búsqueda
        self.search_bar = SearchBar(self)
        container_layout.addWidget(self.search_bar)

        # Buffer oculto para búsqueda en PDF (el texto extraído se vuelca aquí).
        from PyQt5.QtWidgets import QTextEdit as _QTE
        self._pdf_search_buffer = _QTE(self)
        self._pdf_search_buffer.setVisible(False)
        self._pdf_texts = []

        self.viewer_stack = QStackedWidget(self)
        self.md_view = TextViewer(self)
        self.pdf_scroll = PdfViewer(self)

        self.viewer_stack.addWidget(self.md_view)
        self.viewer_stack.addWidget(self.pdf_scroll)
        self.search_bar.set_target(self.md_view)
        container_layout.addWidget(self.viewer_stack)

        # --- Barra de lectura flotante (solo visible con documento) ---
        self.reading_overlay = Toolbar.setup_reading_overlay(self.viewer_stack, self)
        container_layout.addWidget(self.reading_overlay)

        # Conectar scrolls para progreso
        self.md_view.verticalScrollBar().valueChanged.connect(self._update_progress)
        self.pdf_scroll.verticalScrollBar().valueChanged.connect(self._update_progress)

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
        update_window_position(self, "left")

    def _toggle_control_panel(self):
        """Muestra/oculta manualmente el panel de controles (botón o Ctrl + P)."""
        self.control_panel.setVisible(not self.control_panel.isVisible())
        self.adjustSize()

    def _show_shortcuts(self):
        if hasattr(self, "_shortcuts_dialog") and self._shortcuts_dialog.isVisible():
            self._shortcuts_dialog.raise_()
            self._shortcuts_dialog.activateWindow()
            return
        from .ui.shortcuts_dialog import ShortcutsDialog
        self._shortcuts_dialog = ShortcutsDialog(self.tema_actual, self)
        self._shortcuts_dialog.show()
        self._shortcuts_dialog.raise_()
        self._shortcuts_dialog.activateWindow()

    def _restart_autoscroll(self):
        self.auto_scroll.reset()
        self._sync_autoscroll_button()
        viewer = self.viewer_stack.currentWidget()
        if viewer:
            viewer.verticalScrollBar().setValue(0)
        self.reading_restart_btn.hide()
        self._update_progress()

    def _update_progress(self):
        viewer = self.viewer_stack.currentWidget()
        if not viewer:
            return
        scrollbar = viewer.verticalScrollBar()
        if not scrollbar or scrollbar.maximum() == 0:
            self.reading_progress_label.setText("")
            return
        if viewer == self.pdf_scroll:
            page = len(self._pdf_texts)
            if page > 0:
                current_val = scrollbar.value()
                max_val = scrollbar.maximum()
                ratio = current_val / max_val if max_val > 0 else 0
                current_page = max(1, int(ratio * page) + 1)
                self.reading_progress_label.setText("Pág. %d/%d" % (current_page, page))
                return
        val = scrollbar.value()
        max_val = scrollbar.maximum()
        pct = int((val / max_val) * 100) if max_val > 0 else 100
        self.reading_progress_label.setText("%d%%" % pct)

    def toggle_collapsed(self):
        self._animate_toggle_collapsed()
        self.edge_button.setToolTip("Expandir\nAtajo: Ctrl + H" if self.is_collapsed else "Colapsar\nAtajo: Ctrl + H")
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
            self.capture_button.setToolTip("Visible en captura\nAtajo: Ctrl + Shift + C")
        else:
            self.capture_button.setIcon(get_icon("eye_off"))
            self.capture_button.setToolTip("Oculto en captura\nAtajo: Ctrl + Shift + C")

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
        self._opacity = value
        self.opacity_pct_label.setText(f"{value}%")
        ui_settings.set("script_opacity", value)
        self._apply_global_opacity()

    def _sync_autoscroll_button(self):
        if self.auto_scroll.is_active:
            self.scroll_play_btn.setIcon(get_icon("pause"))
            self.scroll_play_btn.setToolTip("Pausar desplazamiento\nAtajo: Espacio")
            self.scroll_status_label.setText("▶ Desplazando")
            self.reading_play_btn.setIcon(get_icon("pause"))
            self.reading_play_btn.setToolTip("Pausar desplazamiento\nAtajo: Espacio")
        else:
            self.scroll_play_btn.setIcon(get_icon("play"))
            self.scroll_play_btn.setToolTip("Iniciar desplazamiento automático\nAtajo: Espacio")
            self.scroll_status_label.setText("⏸ Pausado")
            self.reading_play_btn.setIcon(get_icon("play"))
            self.reading_play_btn.setToolTip("Reproducir desplazamiento\nAtajo: Espacio")

    def _on_autoscroll_stopped(self):
        self._sync_autoscroll_button()
        self.reading_play_btn.setIcon(get_icon("play"))
        self.reading_play_btn.setToolTip("Reproducir desplazamiento\nAtajo: Espacio")
        viewer = self.viewer_stack.currentWidget()
        scrollbar = viewer.verticalScrollBar() if viewer else None
        if scrollbar and scrollbar.value() >= scrollbar.maximum():
            self.scroll_status_label.setText("✓ Fin del documento")
            self.reading_progress_label.setText("Fin")
            self.reading_restart_btn.show()

    def _toggle_autoscroll(self):
        self.auto_scroll.toggle()
        self._sync_autoscroll_button()
        if self.auto_scroll.is_active:
            self.reading_restart_btn.hide()

    def _autoscroll_faster(self):
        old = self.auto_scroll.speed
        self.auto_scroll.speed += 1
        new = self.auto_scroll.speed
        s = str(new)
        if new == old:
            s = "↥" + s
            QTimer.singleShot(600, self._clear_speed_bound)
        self.scroll_speed_label.setText(s)
        self.reading_speed_label.setText(s)

    def _autoscroll_slower(self):
        old = self.auto_scroll.speed
        self.auto_scroll.speed -= 1
        new = self.auto_scroll.speed
        s = str(new)
        if new == old:
            s = "↧" + s
            QTimer.singleShot(600, self._clear_speed_bound)
        self.scroll_speed_label.setText(s)
        self.reading_speed_label.setText(s)

    def _clear_speed_bound(self):
        self.scroll_speed_label.setText(str(self.auto_scroll.speed))
        self.reading_speed_label.setText(str(self.auto_scroll.speed))

    def _apply_global_opacity(self):
        self.setWindowOpacity(self._opacity / 100.0)
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(self._opacity)
        self.opacity_slider.blockSignals(False)
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

        self.auto_scroll.reset()
        self.scroll_play_btn.setIcon(get_icon("play"))
        self.scroll_play_btn.setToolTip("Iniciar desplazamiento automático\nAtajo: Espacio")
        self.scroll_speed_label.setText(str(self.auto_scroll.speed))
        self.reading_speed_label.setText(str(self.auto_scroll.speed))

        self.reading_overlay.setVisible(True)

        # Volcar texto de PDF al buffer de búsqueda si es necesario.
        is_pdf = self.viewer_stack.currentWidget() == self.pdf_scroll
        if is_pdf and hasattr(self, "_pdf_texts") and self._pdf_texts:
            self._pdf_search_buffer.setPlainText("\n".join(self._pdf_texts))
        
        # Scroll to top
        if self.viewer_stack.currentWidget() == self.md_view:
            self.md_view.verticalScrollBar().setValue(0)
        else:
            self.pdf_scroll.verticalScrollBar().setValue(0)

        self._update_progress()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                p = urls[0].toLocalFile()
                if p.lower().endswith((".md", ".markdown", ".pdf", ".txt")):
                    event.acceptProposedAction()
                    return
        event.ignore()
        self.path_label.setText("Formato no compatible — usa .md, .pdf o .txt")

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

    def closeEvent(self, event):
        if hasattr(self, "auto_scroll") and self.auto_scroll.is_active:
            self.auto_scroll.stop()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.search_bar.isVisible():
                self.search_bar.hide_bar()
            else:
                if self.auto_scroll.is_active:
                    from PyQt5.QtWidgets import QMessageBox
                    reply = QMessageBox.question(self, "HelPy — Guion",
                        "El desplazamiento automático está activo.\n¿Cerrar la ventana del guion?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply != QMessageBox.Yes:
                        return
                self.close()
            return
        if event.key() == Qt.Key_O and event.modifiers() & Qt.ControlModifier:
            self.open_script_file()
            return
        if event.key() == Qt.Key_P and event.modifiers() & Qt.ControlModifier:
            self._toggle_control_panel()
            return
        if event.key() == Qt.Key_H and event.modifiers() & Qt.ControlModifier:
            self.toggle_collapsed()
            return
        if event.key() == Qt.Key_C and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self.toggle_capture_visibility()
            return
        if event.key() == Qt.Key_F and event.modifiers() & Qt.ControlModifier:
            is_pdf = self.viewer_stack.currentWidget() == self.pdf_scroll
            target = self._pdf_search_buffer if is_pdf else self.md_view
            self.search_bar.set_target(target)
            self.search_bar.toggle()
            return
        # Autoscroll por teclado: Space = play/pause, Up/Down = velocidad
        if event.key() == Qt.Key_Space:
            if not self.search_bar.isVisible():
                self._toggle_autoscroll()
            return
        if event.key() == Qt.Key_Up:
            self._autoscroll_faster()
            return
        if event.key() == Qt.Key_Down:
            self._autoscroll_slower()
            return
        if event.key() == Qt.Key_0 and event.modifiers() & Qt.ControlModifier:
            self.zoom_manager.zoom_factor = 1.0
            self.zoom_manager.apply_text_zoom()
            return
        super().keyPressEvent(event)

    def _apply_settings(self):
        self._update_capture_button()
        self._apply_capture_affinity()

        if self.is_collapsed:
            self.container.setVisible(False)
            self.edge_button.setIcon(get_icon("expand"))
            self.edge_button.setToolTip("Expandir\nAtajo: Ctrl + H")
        else:
            self.container.setVisible(True)
            self.edge_button.setIcon(get_icon("collapse"))
            self.edge_button.setToolTip("Colapsar\nAtajo: Ctrl + H")

        if self._last_script_path and os.path.exists(self._last_script_path):
            self.file_loader.load_script(self._last_script_path)

        self.adjustSize()

    def _apply_styles(self):
        self.setStyleSheet(obtener_qss(self.tema_actual))
        self.opacity_slider.style().unpolish(self.opacity_slider)
        self.opacity_slider.style().polish(self.opacity_slider)
        self.opacity_pct_label.style().unpolish(self.opacity_pct_label)
        self.opacity_pct_label.style().polish(self.opacity_pct_label)
