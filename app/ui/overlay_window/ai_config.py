import os
import json
import time
import threading
from pathlib import Path
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QFormLayout, QLineEdit, QWidget, QLabel, QFileDialog
)
from PyQt5.QtCore import QTimer, pyqtSignal
from app.core.llm_client import get_llm_client
from app.utils.path_utils import writable_config_path
from app.ui.themes import PALETAS, normalizar_tema
from app.ui.shared import get_icon
from app.ui.shared.spinner import LoadingSpinner
from app.ui.overlay_window.hotkeys import HOTKEY_DESCRIPTIONS, DEFAULT_HOTKEYS
from app.ui.overlay_window.hotkey_button import HotkeyRow
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AIConfigPanel(QFrame):
    download_finished = pyqtSignal(str, bool)  # (message, success)
    download_progress = pyqtSignal(int, int)   # (bytes_descargados, bytes_total; 0 = desconocido)

    def __init__(self, settings, theme_manager, overlay, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.theme_manager = theme_manager
        self._overlay = overlay
        self.setObjectName("aiConfigGroup")
        self._download_cancel_event = threading.Event()
        self._download_busy = False
        self._download_started = 0.0
        self.download_finished.connect(self._on_download_finished)
        self.download_progress.connect(self._on_download_progress)
        
        self.llm_config_collapsed = bool(self.settings.get("llm_config_collapsed", False))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header Row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        self.llm_toggle_button = QPushButton("Configurar la IA:", self)
        self.llm_toggle_button.setObjectName("sectionToggle")
        self.llm_toggle_button.setToolTip("Mostrar/ocultar configuración del modelo de IA")
        self.llm_toggle_button.clicked.connect(self.toggle_llm_config)
        
        header_row.addWidget(self.llm_toggle_button, 0)
        header_row.addStretch(1)
        layout.addLayout(header_row)

        # Body
        self.ai_config_body = QFrame(self)
        self.ai_config_body.setObjectName("aiConfigBody")
        body_layout = QVBoxLayout(self.ai_config_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(12, 8, 12, 12)

        # --- STT Config ---
        self.stt_provider_combo = QComboBox(self)
        self.stt_provider_combo.addItems(["Google (Nube)", "Local (faster-whisper)"])
        self.stt_provider_combo.setToolTip("Motor que convierte tu voz en texto")
        form_layout.addRow("Transcripción de voz:", self.stt_provider_combo)

        self.whisper_model_combo = QComboBox(self)
        self.whisper_model_combo.addItems(["tiny", "base", "small"])
        self.whisper_model_combo.setToolTip("Modelo Whisper: tiny (rápido) → small (más preciso)")
        form_layout.addRow("Modelo Whisper:", self.whisper_model_combo)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line)

        # --- LLM Config ---
        self.ai_provider_combo = QComboBox(self)
        self.ai_provider_combo.setObjectName("deviceCombo")
        self.ai_provider_combo.addItems(["LM Studio", "Google", "Groq", "Local (llama.cpp)"])
        self.ai_provider_combo.setToolTip("Proveedor del modelo de IA")
        form_layout.addRow("Proveedor:", self.ai_provider_combo)

        self.api_key_input = QLineEdit(self)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setToolTip("Clave de API del proveedor (no necesaria en LM Studio ni en modo local)")
        form_layout.addRow("Clave de API:", self.api_key_input)

        self.model_id_input = QLineEdit(self)
        self.model_id_input.setPlaceholderText("Opcional: openai/gpt-oss-120b")
        self.model_id_input.setToolTip("ID del modelo o ruta al archivo .gguf para modo local")
        
        model_container = QWidget(self)
        model_row = QHBoxLayout(model_container)
        model_row.setContentsMargins(0, 0, 0, 0)
        model_row.addWidget(self.model_id_input, 1)
        
        self.browse_model_btn = QPushButton("Examinar...", self)
        self.browse_model_btn.setToolTip("Seleccionar archivo de modelo .gguf local")
        self.browse_model_btn.clicked.connect(self._browse_model)
        self.download_model_btn = QPushButton("Descargar modelo", self)
        self.download_model_btn.setObjectName("downloadModelBtn")
        self.download_model_btn.setToolTip("Descargar modelo Gemma 3 1B (769 MB)")
        self.download_model_btn.clicked.connect(self._download_model)
        self.download_model_btn.setVisible(False)
        
        self.download_spinner = LoadingSpinner(self, size=14, line_width=2, speed=40)

        model_row.addWidget(self.browse_model_btn, 0)
        model_row.addWidget(self.download_spinner, 0)
        model_row.addWidget(self.download_model_btn, 0)
        form_layout.addRow("Modelo:", model_container)

        button_row = QHBoxLayout()
        self.save_spinner = LoadingSpinner(self, size=14, line_width=2, speed=40)
        self.save_ai_button = QPushButton("Guardar", self)
        self.save_ai_button.setObjectName("saveAIButton")
        self.save_ai_button.setToolTip("Guardar configuración de proveedor y modelo")
        self.save_ai_button.clicked.connect(self._save_ai_settings)
        self.ai_status_label = QLabel("", self)
        self.ai_status_label.setObjectName("statusLabel")
        button_row.addWidget(self.save_spinner, 0)
        button_row.addWidget(self.ai_status_label, 1)
        button_row.addWidget(self.save_ai_button)

        body_layout.addLayout(form_layout)
        body_layout.addLayout(button_row)
        layout.addWidget(self.ai_config_body)
        
        # --- Apariencia Section (tema visual fuera de la config de IA) ---
        self.apariencia_config_collapsed = bool(self.settings.get("apariencia_config_collapsed", False))
        
        self.apariencia_toggle_button = QPushButton("Apariencia:", self)
        self.apariencia_toggle_button.setObjectName("sectionToggle")
        self.apariencia_toggle_button.setToolTip("Tema visual y modo claro/oscuro")
        self.apariencia_toggle_button.clicked.connect(self.toggle_apariencia_config)
        layout.addWidget(self.apariencia_toggle_button)
        
        self.selector_temas = QComboBox(self)
        self.selector_temas.setObjectName("deviceCombo")
        self.selector_temas.setToolTip("Seleccionar tema visual de la interfaz")
        self.selector_temas.currentIndexChanged.connect(self._on_tema_selected)
        
        self.apariencia_config_body = QFrame(self)
        self.apariencia_config_body.setObjectName("aiConfigBody")
        apariencia_layout = QHBoxLayout(self.apariencia_config_body)
        apariencia_layout.setContentsMargins(12, 8, 12, 12)
        apariencia_layout.setSpacing(8)
        tema_label = QLabel("Tema:", self)
        tema_label.setObjectName("metaLabel")
        apariencia_layout.addWidget(tema_label)
        apariencia_layout.addWidget(self.selector_temas, 1)
        layout.addWidget(self.apariencia_config_body)
        
        self._poblar_inicial()
        
        # --- Hotkey Config Section ---
        self.hotkey_config_collapsed = bool(self.settings.get("hotkey_config_collapsed", False))
        
        self.hotkey_toggle_button = QPushButton("Atajos de teclado:", self)
        self.hotkey_toggle_button.setObjectName("sectionToggle")
        self.hotkey_toggle_button.setToolTip("Configurar atajos de teclado personalizados")
        self.hotkey_toggle_button.clicked.connect(self.toggle_hotkey_config)
        layout.addWidget(self.hotkey_toggle_button)
        
        self.hotkey_config_body = QFrame(self)
        self.hotkey_config_body.setObjectName("aiConfigBody")
        hotkey_body_layout = QVBoxLayout(self.hotkey_config_body)
        hotkey_body_layout.setContentsMargins(0, 0, 0, 0)
        
        hotkey_form = QFormLayout()
        hotkey_form.setSpacing(8)
        hotkey_form.setContentsMargins(12, 8, 12, 12)
        
        self.hotkey_inputs = {}
        for action, description in HOTKEY_DESCRIPTIONS.items():
            row = HotkeyRow(action, description, self)
            self.hotkey_inputs[action] = row
            hotkey_form.addRow(f"{description}:", row)
        
        hotkey_button_row = QHBoxLayout()
        self.save_hotkeys_btn = QPushButton("Guardar atajos", self)
        self.save_hotkeys_btn.setObjectName("saveButton")
        self.save_hotkeys_btn.setToolTip("Validar y guardar los atajos de teclado")
        self.save_hotkeys_btn.clicked.connect(self._save_hotkeys_clicked)
        self.reset_hotkeys_btn = QPushButton("Restaurar atajos", self)
        self.reset_hotkeys_btn.setToolTip("Restaurar los atajos de teclado originales")
        self.reset_hotkeys_btn.clicked.connect(self._reset_hotkeys)
        self.hotkey_status_label = QLabel("", self)
        self.hotkey_status_label.setObjectName("statusLabel")
        hotkey_button_row.addWidget(self.hotkey_status_label, 1)
        hotkey_button_row.addWidget(self.save_hotkeys_btn)
        hotkey_button_row.addWidget(self.reset_hotkeys_btn)
        
        hotkey_body_layout.addLayout(hotkey_form)
        hotkey_body_layout.addLayout(hotkey_button_row)
        layout.addWidget(self.hotkey_config_body)
        
        # Connectors
        self.stt_provider_combo.currentIndexChanged.connect(self._on_stt_provider_changed)
        self.ai_provider_combo.currentIndexChanged.connect(self._on_ai_provider_changed)
        
        self._load_ai_settings()
        self._load_hotkey_settings()
        self._apply_llm_config_visibility()
        self._apply_apariencia_config_visibility()
        self._apply_hotkey_config_visibility()
        self._aplicar_tema_inicial()

    def reload_icons(self):
        self.llm_toggle_button.setIcon(get_icon("expand") if self.llm_config_collapsed else get_icon("collapse"))
        self.apariencia_toggle_button.setIcon(
            get_icon("expand") if self.apariencia_config_collapsed else get_icon("collapse"))

    def toggle_llm_config(self):
        self.llm_config_collapsed = not self.llm_config_collapsed
        self.settings.set("llm_config_collapsed", self.llm_config_collapsed)
        self._apply_llm_config_visibility()

    def _apply_llm_config_visibility(self):
        self.ai_config_body.setVisible(not self.llm_config_collapsed)
        self.llm_toggle_button.setIcon(get_icon("expand") if self.llm_config_collapsed else get_icon("collapse"))
        if self.parentWidget() and hasattr(self.parentWidget(), "adjustSize"):
            self.parentWidget().adjustSize()
        window = self.window()
        if window and hasattr(window, "adjustSize"):
            window.adjustSize()

    def toggle_hotkey_config(self):
        self.hotkey_config_collapsed = not self.hotkey_config_collapsed
        self.settings.set("hotkey_config_collapsed", self.hotkey_config_collapsed)
        self._apply_hotkey_config_visibility()

    def toggle_apariencia_config(self):
        self.apariencia_config_collapsed = not self.apariencia_config_collapsed
        self.settings.set("apariencia_config_collapsed", self.apariencia_config_collapsed)
        self._apply_apariencia_config_visibility()

    def _apply_apariencia_config_visibility(self):
        self.apariencia_config_body.setVisible(not self.apariencia_config_collapsed)
        self.apariencia_toggle_button.setIcon(
            get_icon("expand") if self.apariencia_config_collapsed else get_icon("collapse"))
        if self.parentWidget() and hasattr(self.parentWidget(), "adjustSize"):
            self.parentWidget().adjustSize()
        window = self.window()
        if window and hasattr(window, "adjustSize"):
            window.adjustSize()

    def _apply_hotkey_config_visibility(self):
        self.hotkey_config_body.setVisible(not self.hotkey_config_collapsed)
        self.hotkey_toggle_button.setIcon(get_icon("expand") if self.hotkey_config_collapsed else get_icon("collapse"))
        if self.parentWidget() and hasattr(self.parentWidget(), "adjustSize"):
            self.parentWidget().adjustSize()
        window = self.window()
        if window and hasattr(window, "adjustSize"):
            window.adjustSize()

    def _load_hotkey_settings(self):
        hotkeys = self.settings.get("hotkeys", {})
        for action, row in self.hotkey_inputs.items():
            current = hotkeys.get(action, DEFAULT_HOTKEYS.get(action, ""))
            row.set_pynput_hotkey(current)

    def _reset_hotkeys(self):
        for action, row in self.hotkey_inputs.items():
            row.set_pynput_hotkey(DEFAULT_HOTKEYS.get(action, ""))
        
        window = self._overlay
        if window and hasattr(window, "hotkey_manager"):
            window.hotkey_manager.reset_hotkeys()
        
        self.hotkey_status_label.setProperty("level", "warning")
        self.hotkey_status_label.style().unpolish(self.hotkey_status_label)
        self.hotkey_status_label.style().polish(self.hotkey_status_label)
        self.hotkey_status_label.setText("Atajos restaurados")
        QTimer.singleShot(2000, lambda: self.hotkey_status_label.setText(""))

    def _on_tema_selected(self, index):
        full_key = self.selector_temas.itemData(index)
        if full_key:
            self.theme_manager.cambiar_tema_interfaz(full_key)
            self._actualizar_tooltip_tema(full_key)

    def _actualizar_tooltip_tema(self, full_key):
        """Preview vivo del tema en el tooltip del combo: fondo, acento y texto."""
        t = PALETAS.get(full_key)
        if not t:
            return
        self.selector_temas.setToolTip(
            f"Fondo: {t['fondo']}  ·  "
            f"Acento: {t['acento']}  ·  "
            f"Texto: {t['texto']}"
        )

    def _poblar_inicial(self):
        # Todas las paletas en un solo combo, separadas por familia.
        orden_familias = ("(Clásico)", "(Oscuro)", "(Claro)")
        self.selector_temas.blockSignals(True)
        self.selector_temas.clear()
        for idx_fam, sufijo in enumerate(orden_familias):
            if idx_fam > 0:
                self.selector_temas.insertSeparator(self.selector_temas.count())
            for full_key in PALETAS:
                if sufijo in full_key:
                    self.selector_temas.addItem(full_key.replace(sufijo, "").strip(), full_key)
        self.selector_temas.blockSignals(False)

    def _aplicar_tema_inicial(self):
        tema_guardado = normalizar_tema(self.settings.get("tema", "Slate Minimalist (Clásico)"))
        full_keys = [self.selector_temas.itemData(i) for i in range(self.selector_temas.count())]
        self.selector_temas.blockSignals(True)
        if tema_guardado in full_keys:
            self.selector_temas.setCurrentIndex(full_keys.index(tema_guardado))
            nuevo_tema = tema_guardado
        elif full_keys:
            self.selector_temas.setCurrentIndex(0)
            nuevo_tema = self.selector_temas.itemData(0)
        else:
            self.selector_temas.blockSignals(False)
            return
        self.selector_temas.blockSignals(False)
        self.theme_manager.cambiar_tema_interfaz(nuevo_tema)
        self._actualizar_tooltip_tema(nuevo_tema)

    def _get_config_path(self, filename="config.json"):
        return writable_config_path(filename)

    def _on_stt_provider_changed(self, index):
        provider = self.stt_provider_combo.currentText()
        if "Local" in provider:
            self.whisper_model_combo.setVisible(True)
        else:
            self.whisper_model_combo.setVisible(False)

    def _on_ai_provider_changed(self, index):
        stt_provider_ui = self.stt_provider_combo.currentText()
        stt_provider = "whisper" if "Local" in stt_provider_ui else "google"
        whisper_model = self.whisper_model_combo.currentText()
        provider = self.ai_provider_combo.currentText()
        if provider == "Local (llama.cpp)":
            self.api_key_input.setVisible(False)
            self.model_id_input.setPlaceholderText("Ruta al modelo .gguf")
            self.browse_model_btn.setVisible(True)
            model_id = self.model_id_input.text().strip()
            if model_id:
                model_path = Path(model_id)
                if not model_path.is_absolute():
                    from app.utils.path_utils import resource_path
                    model_path = Path(resource_path(model_id))
                self.download_model_btn.setVisible(not model_path.exists())
            else:
                self.download_model_btn.setVisible(True)
        else:
            self.api_key_input.setVisible(True)
            self.browse_model_btn.setVisible(False)
            self.download_model_btn.setVisible(False)
            if provider == "Groq":
                self.model_id_input.setPlaceholderText("Opcional: openai/gpt-oss-120b")
            elif provider == "Google":
                self.model_id_input.setPlaceholderText("gemini-3.1-flash-lite")
            else:
                self.model_id_input.setPlaceholderText("ID del modelo")

    def _load_ai_settings(self):
        path = self._get_config_path()
        if not os.path.exists(path):
            return

        try:
            with open(path, "r", encoding="utf-8") as handle:
                ai_settings = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return

        # STT Settings
        stt_provider = ai_settings.get("stt_provider", "google")
        whisper_model = ai_settings.get("whisper_model", "tiny")
        if stt_provider == "whisper":
            self.stt_provider_combo.setCurrentText("Local (faster-whisper)")
            self.whisper_model_combo.setVisible(True)
        else:
            self.stt_provider_combo.setCurrentText("Google (Nube)")
            self.whisper_model_combo.setVisible(False)
        self.whisper_model_combo.setCurrentText(whisper_model)

        # Normalize: "Local" in config -> "Local (llama.cpp)" in UI combo
        provider_raw = ai_settings.get("provider", "LM Studio")
        provider = "Local (llama.cpp)" if provider_raw == "Local" else provider_raw
        api_key = ai_settings.get("api_key", "")
        model_id = ai_settings.get("model_id", "")

        self.ai_provider_combo.setCurrentText(provider)
        self.api_key_input.setText(api_key)
        self.model_id_input.setText(model_id)

        if provider == "Local (llama.cpp)":
            self.api_key_input.setVisible(False)
            self.model_id_input.setPlaceholderText("Ruta al modelo .gguf")
            self.browse_model_btn.setVisible(True)
        else:
            self.api_key_input.setVisible(True)
            self.browse_model_btn.setVisible(False)

    def _set_ai_status(self, text, level="default"):
        self.ai_status_label.setProperty("level", level)
        self.ai_status_label.style().unpolish(self.ai_status_label)
        self.ai_status_label.style().polish(self.ai_status_label)
        self.ai_status_label.setText(text)

    def _save_ai_settings(self):
        self.save_spinner.start()
        self.save_ai_button.setEnabled(False)
        self.save_ai_button.setText("Guardando...")
        self._set_ai_status("Guardando...")

        def do_save():
            path = self._get_config_path()
            folder = os.path.dirname(path)
            os.makedirs(folder, exist_ok=True)

            stt_provider_ui = self.stt_provider_combo.currentText()
            stt_provider = "whisper" if "Local" in stt_provider_ui else "google"
            whisper_model = self.whisper_model_combo.currentText()
            provider = self.ai_provider_combo.currentText()
            api_key = self.api_key_input.text()
            model_id = self.model_id_input.text().strip()

            if provider == "Local (llama.cpp)":
                provider = "Local"
            if provider == "Google" and not model_id:
                model_id = "gemini-3.1-flash-lite"
            if provider == "Groq" and not model_id:
                model_id = "openai/gpt-oss-120b"

            ai_settings = {
                "stt_provider": stt_provider,
                "whisper_model": whisper_model,
                "provider": provider,
                "api_key": api_key,
                "model_id": model_id,
            }

            try:
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(ai_settings, handle, indent=2)
                self._set_ai_status("Configuración guardada")
                get_llm_client().reload()
                window = self._overlay
                if hasattr(window, "assistant"):
                    started, was_running = window.assistant.set_stt_settings(stt_provider, whisper_model)
                    if was_running and not started and hasattr(window, "_reset_recording_state"):
                        window._reset_recording_state()
            except OSError:
                self._set_ai_status("No se pudo guardar. Revisa los permisos de la carpeta.", "error")
            finally:
                self.save_spinner.stop()
                self.save_ai_button.setEnabled(True)
                self.save_ai_button.setText("Guardar")

        QTimer.singleShot(150, do_save)

    @staticmethod
    def _validar_hotkey(value: str):
        """Devuelve None si el formato es parseable por pynput, o un mensaje de error."""
        try:
            from pynput import keyboard as kb
            kb.HotKey.parse(value)
            return None
        except Exception:
            return f"Formato inválido: {value}"

    def _save_hotkey_settings(self):
        """Valida (inline por campo) y guarda las hotkeys de forma atómica."""
        hotkeys = {}
        invalid_count = 0
        for action, row in self.hotkey_inputs.items():
            value = row.get_pynput_hotkey().strip()
            error = None
            if not value:
                error = "El atajo no puede estar vacío."
            elif (format_error := self._validar_hotkey(value)):
                error = format_error
            elif value in hotkeys.values():
                error = "Ya está asignado a otro atajo."
            if error:
                row.set_invalid(error)
            else:
                row._clear_invalid()
            if error:
                invalid_count += 1
                continue
            hotkeys[action] = value

        if invalid_count:
            self.hotkey_status_label.setText(
                f"No se guardaron: {invalid_count} atajo(s) inválido(s). Revisa los campos marcados."
            )
            self.hotkey_status_label.setProperty("level", "error")
            self.hotkey_status_label.style().unpolish(self.hotkey_status_label)
            self.hotkey_status_label.style().polish(self.hotkey_status_label)
            QTimer.singleShot(4000, lambda: self.hotkey_status_label.setText(""))
            return False

        # Aplicar al hotkey manager; si algo falla, revertir lo aplicado
        window = self._overlay
        manager = window.hotkey_manager if window and hasattr(window, "hotkey_manager") else None
        if manager:
            previous = manager.get_current_hotkeys()
            applied = []
            failed = False
            for action, value in hotkeys.items():
                if manager.update_hotkey(action, value):
                    applied.append(action)
                else:
                    failed = True
                    break
            if failed:
                for action in applied:
                    manager.update_hotkey(
                        action, previous.get(action, DEFAULT_HOTKEYS.get(action, ""))
                    )
                self.hotkey_status_label.setProperty("level", "error")
                self.hotkey_status_label.style().unpolish(self.hotkey_status_label)
                self.hotkey_status_label.style().polish(self.hotkey_status_label)
                self.hotkey_status_label.setText(
                    "No se pudieron guardar todos los atajos. Inténtalo de nuevo."
                )
                QTimer.singleShot(4000, lambda: self.hotkey_status_label.setText(""))
                return False

        # Persistir solo tras éxito total
        self.settings.set("hotkeys", hotkeys)
        
        self.hotkey_status_label.setProperty("level", "default")
        self.hotkey_status_label.style().unpolish(self.hotkey_status_label)
        self.hotkey_status_label.style().polish(self.hotkey_status_label)
        self.hotkey_status_label.setText("Atajos guardados")
        QTimer.singleShot(2000, lambda: self.hotkey_status_label.setText(""))
        return True

    def _save_hotkeys_clicked(self):
        """Botón 'Guardar atajos': valida y guarda con feedback inline."""
        self._save_hotkey_settings()

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar modelo GGUF", "", "Modelos GGUF (*.gguf)"
        )
        if path:
            self.model_id_input.setText(path)

    def _download_model(self):
        if self._download_busy:
            self._cancel_download()
            return

        from huggingface_hub import hf_hub_download
        from app.utils.path_utils import writable_models_dir

        self._download_busy = True
        self._download_cancel_event = threading.Event()
        self._download_started = time.monotonic()
        self.download_model_btn.setText("Cancelar")
        self.download_model_btn.setToolTip("Cancelar la descarga del modelo")
        self.download_spinner.start()
        self._set_ai_status("Descargando modelo (769 MB)...")

        model_dir = Path(writable_models_dir())

        tqdm_class = self._build_download_tqdm_class(
            self._download_cancel_event, self._emit_progress
        )

        def _worker():
            try:
                hf_hub_download(
                    repo_id="google/gemma-3-1b-it-GGUF",
                    filename="gemma-3-1b-it-Q4_K_M.gguf",
                    local_dir=str(model_dir),
                    tqdm_class=tqdm_class,
                )
                if self._download_cancel_event.is_set():
                    self.download_finished.emit("Descarga cancelada", False)
                else:
                    self.download_finished.emit("Descarga completada!", True)
            except Exception:
                logger.exception("Error al descargar el modelo Gemma")
                if self._download_cancel_event.is_set():
                    self.download_finished.emit("Descarga cancelada", False)
                else:
                    self.download_finished.emit(
                        "No se pudo descargar el modelo. "
                        "Revisa la conexión a internet e inténtalo de nuevo.",
                        False,
                    )

        threading.Thread(target=_worker, daemon=True).start()

    def _build_download_tqdm_class(self, cancel_event, on_progress):
        from huggingface_hub.utils import tqdm as hf_tqdm

        class _DownloadCanceled(Exception):
            pass

        class _HelPyDownloadTqdm(hf_tqdm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._cancel_event = cancel_event
                self._on_progress = on_progress
                self._bytes_done = 0
                self._bytes_total = kwargs.get("total")

            def update(self, n=1):
                if self._cancel_event is not None and self._cancel_event.is_set():
                    raise _DownloadCanceled()
                self._bytes_done += n
                super().update(n)
                if self._on_progress is not None:
                    self._on_progress(self._bytes_done, self._bytes_total)

        return _HelPyDownloadTqdm

    def _emit_progress(self, bytes_done, bytes_total):
        self.download_progress.emit(int(bytes_done), int(bytes_total) or 0)

    def _on_download_progress(self, bytes_done, bytes_total):
        if not self._download_busy:
            return
        # Tras cancelar, los ticks tardíos no deben sobrescribir "Cancelando descarga...".
        if self._download_cancel_event.is_set():
            return
        mb_done = bytes_done / (1024 * 1024)
        if bytes_total > 0:
            mb_total = bytes_total / (1024 * 1024)
            percent = (bytes_done / bytes_total) * 100
            elapsed = max(time.monotonic() - self._download_started, 0.001)
            rate = bytes_done / elapsed
            if rate > 0 and bytes_done < bytes_total:
                eta_seconds = (bytes_total - bytes_done) / rate
                eta_text = self._format_eta(eta_seconds)
                self.ai_status_label.setText(
                    f"Descargando: {mb_done:.0f} / {mb_total:.0f} MB ({percent:.0f}%) "
                    f"· restan {eta_text}"
                )
            else:
                self.ai_status_label.setText(
                    f"Descargando: {mb_done:.0f} / {mb_total:.0f} MB ({percent:.0f}%)"
                )
        else:
            self.ai_status_label.setText(f"Descargando: {mb_done:.0f} MB...")

    @staticmethod
    def _format_eta(seconds):
        seconds = max(int(seconds), 0)
        if seconds < 60:
            return f"{seconds}s"
        if seconds < 3600:
            return f"{seconds // 60}m {seconds % 60:02d}s"
        return f"{seconds // 3600}h {seconds % 3600 // 60:02d}m"

    def _cancel_download(self):
        self._download_cancel_event.set()
        self.download_model_btn.setEnabled(False)
        self.ai_status_label.setText("Cancelando descarga...")

    def _on_download_finished(self, message: str, success: bool):
        self._download_busy = False
        self.download_spinner.stop()
        self.download_model_btn.setEnabled(True)
        self.download_model_btn.setText("Descargar modelo")
        self.download_model_btn.setToolTip("Descargar modelo Gemma 3 1B (769 MB)")
        self._set_ai_status(message)
        if success:
            from app.utils.path_utils import writable_models_dir
            dest = Path(writable_models_dir()) / "gemma-3-1b-it-Q4_K_M.gguf"
            self.model_id_input.setText(str(dest))
            self.download_model_btn.setVisible(False)
