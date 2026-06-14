import os
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTextEdit, QApplication
)

from app.utils.text_extractor import extraer_texto
from app.core.llm_client import get_llm_client
from app.ui.shared.spinner import LoadingSpinner


class ContextPanel(QFrame):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._context_path = settings.get("context_path", "")
        self.setObjectName("contextGroup")

        self._collapsed = bool(settings.get("context_collapsed", True))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toggle_button = QPushButton("Contexto", self)
        self.toggle_button.setObjectName("sectionToggle")
        self.toggle_button.setFixedWidth(120)
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
        self.load_btn.clicked.connect(self._load_context)
        self.context_spinner = LoadingSpinner(self, size=14, line_width=2, speed=40)
        self.context_spinner.hide()
        self.clear_btn = QPushButton("Limpiar", self)
        self.clear_btn.clicked.connect(self._clear_context)
        btn_row.addWidget(self.load_btn)
        btn_row.addWidget(self.context_spinner)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch(1)
        body_layout.addLayout(btn_row)

        self.path_label = QLabel(self)
        self.path_label.setObjectName("statusLabel")
        self.path_label.setWordWrap(True)
        body_layout.addWidget(self.path_label)

        self.status_label = QLabel(self)
        self.status_label.setObjectName("statusLabel")
        body_layout.addWidget(self.status_label)

        self.preview = QTextEdit(self)
        self.preview.setReadOnly(True)
        self.preview.setObjectName("textArea")
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

    def _restore_context(self):
        if self._context_path and os.path.exists(self._context_path):
            try:
                texto = extraer_texto(self._context_path)
                get_llm_client().set_context(texto)
                self._update_ui(self._context_path, texto)
            except Exception:
                self._context_path = ""
                self.settings.set("context_path", "")
                self._update_ui("", "")

    def _blocking_task(self, task_fn, status_text="Procesando..."):
        self.context_spinner.start()
        self.load_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.status_label.setText(status_text)
        QApplication.processEvents()
        try:
            result = task_fn()
            return result
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            return None
        finally:
            self.context_spinner.stop()
            self.load_btn.setEnabled(True)
            self.clear_btn.setEnabled(True)

    def _load_context(self):
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

        def load():
            return extraer_texto(path)

        texto = self._blocking_task(load, "Cargando contexto...")
        if texto is None:
            return

        self._context_path = path
        self.settings.set("context_path", path)
        get_llm_client().set_context(texto)
        self._update_ui(path, texto)

    def _clear_context(self):
        def clear():
            get_llm_client().clear_context()
            return True

        self._blocking_task(clear, "Limpiando contexto...")
        self._context_path = ""
        self.settings.set("context_path", "")
        self._update_ui("", "")

    def _update_ui(self, path: str, texto: str):
        if not path:
            self.path_label.setText("")
            self.status_label.setText("Contexto: No cargado")
            self.preview.clear()
            return

        self.path_label.setText(path)
        chars = len(texto)
        self.status_label.setText(f"Contexto: Documento cargado ({chars} caracteres)")
        preview_text = texto[:200].strip()
        if len(texto) > 200:
            preview_text += "..."
        self.preview.setPlainText(preview_text)
