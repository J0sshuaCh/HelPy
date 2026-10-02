import os
import threading
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTextEdit, QMessageBox
)
from PyQt5.QtCore import pyqtSignal

from app.utils.text_extractor import extraer_texto
from app.core.llm_client import get_llm_client
from app.ui.shared.spinner import LoadingSpinner
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ContextPanel(QFrame):
    context_loaded = pyqtSignal(str, str)  # (ruta, texto)
    context_failed = pyqtSignal(bool)      # True = restauración silenciosa

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._context_path = settings.get("context_path", "")
        self.setObjectName("contextGroup")

        self._collapsed = bool(settings.get("context_collapsed", True))
        self._busy = False
        self.context_loaded.connect(self._on_context_loaded)
        self.context_failed.connect(self._on_context_failed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toggle_button = QPushButton("Contexto", self)
        self.toggle_button.setObjectName("sectionToggle")
        self.toggle_button.setFixedWidth(120)
        self.toggle_button.setToolTip("Mostrar/ocultar panel de contexto para documentos de referencia")
        self.toggle_button.setAccessibleName("Panel de documento de contexto")
        self.toggle_button.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_button)

        self.body = QFrame(self)
        self.body.setObjectName("contextBody")
        body_layout = QVBoxLayout(self.body)
        body_layout.setContentsMargins(0, 4, 0, 0)
        body_layout.setSpacing(2)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        self.load_btn = QPushButton("Cargar Contexto", self)
        self.load_btn.setToolTip("Cargar documento (.md, .pdf, .txt) como contexto para la IA")
        self.load_btn.setAccessibleName("Cargar documento de contexto")
        self.load_btn.clicked.connect(self._load_context)
        self.context_spinner = LoadingSpinner(self, size=14, line_width=2, speed=40)
        self.context_spinner.hide()
        self.clear_btn = QPushButton("Limpiar", self)
        self.clear_btn.setToolTip("Eliminar el contexto cargado")
        self.clear_btn.setAccessibleName("Limpiar contexto cargado")
        self.clear_btn.clicked.connect(self._clear_context)
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.context_spinner)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch(1)
        body_layout.addLayout(btn_row)

        self.path_label = QLabel(self)
        self.path_label.setObjectName("metaLabel")
        self.path_label.setWordWrap(True)
        body_layout.addWidget(self.path_label)

        self.status_label = QLabel(self)
        self.status_label.setObjectName("metaLabel")
        body_layout.addWidget(self.status_label)

        self.preview = QTextEdit(self)
        self.preview.setReadOnly(True)
        self.preview.setObjectName("textArea")
        self.preview.setAccessibleName("Vista previa del contexto cargado")
        self.preview.setMaximumHeight(60)
        body_layout.addWidget(self.preview)

        layout.addWidget(self.body)

        self._apply_visibility()
        self._restore_context()

    def _toggle(self):
        self._collapsed = not self._collapsed
        self.settings.set("context_collapsed", self._collapsed)
        self._apply_visibility()

    def _apply_visibility(self):
        self.body.setVisible(not self._collapsed)
        win = self.window()
        if win and hasattr(win, "adjustSize"):
            win.adjustSize()

    def _restore_context(self):
        if self._context_path and os.path.exists(self._context_path):
            self._extract_async(self._context_path, silent_failure=True)

    def _extract_async(self, path: str, silent_failure: bool = False):
        """Extrae el texto de un documento en un hilo para no congelar el overlay."""

        def _worker():
            try:
                texto = extraer_texto(path)
            except Exception:
                logger.exception("Error al extraer el contexto")
                self.context_failed.emit(silent_failure)
            else:
                self.context_loaded.emit(path, texto)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_context_loaded(self, path: str, texto: str):
        self._context_path = path
        self.settings.set("context_path", path)
        get_llm_client().set_context(texto)
        self._update_ui(path, texto)
        self._set_busy(False)

    def _on_context_failed(self, silent: bool):
        if silent:
            self._context_path = ""
            self.settings.set("context_path", "")
            self._update_ui("", "")
        else:
            self.status_label.setText(
                "No se pudo cargar el documento. Verifica que el archivo no esté dañado "
                "y que el formato sea compatible (.md, .pdf, .txt)."
            )
        self._set_busy(False)

    def _set_busy(self, busy: bool):
        self._busy = busy
        self.load_btn.setEnabled(not busy)
        self.clear_btn.setEnabled(not busy)
        if busy:
            self.context_spinner.start()
        else:
            self.context_spinner.stop()

    def _load_context(self):
        if self._busy:
            return

        start_dir = ""
        if self._context_path and os.path.exists(self._context_path):
            start_dir = os.path.dirname(self._context_path)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar documento de contexto",
            start_dir,
            "Documentos (*.md *.markdown *.pdf *.txt);;Todos (*.*)",
        )
        if not path:
            return

        self._set_busy(True)
        self.status_label.setText("Cargando contexto...")
        self._extract_async(path)

    def _clear_context(self):
        if self._busy:
            return
        if not self._context_path and not get_llm_client().has_context():
            return

        reply = QMessageBox.question(
            self,
            "Limpiar contexto",
            "Se eliminará el contexto cargado y dejará de usarse en las respuestas de la IA.\n\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        get_llm_client().clear_context()
        self._context_path = ""
        self.settings.set("context_path", "")
        self._update_ui("", "")

    def _update_ui(self, path: str, texto: str):
        if not path:
            self.path_label.setText("")
            self.status_label.setText("Contexto: no cargado")
            self.preview.clear()
            return

        self.path_label.setText(path)
        chars = len(texto)
        self.status_label.setText(f"Contexto: documento cargado ({chars} caracteres)")
        preview_text = texto[:200].strip()
        if len(texto) > 200:
            preview_text += "..."
        self.preview.setPlainText(preview_text)
