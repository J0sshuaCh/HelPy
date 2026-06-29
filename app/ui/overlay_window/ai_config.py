import os
import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
    QFormLayout, QLineEdit, QWidget, QLabel, QFileDialog, QApplication
)
from PyQt5.QtCore import QSize, QTimer
from PyQt5.QtWidgets import QApplication
from app.core.llm_client import get_llm_client
from app.utils.path_utils import writable_config_path
from app.ui.themes import filtrar_temas_por_modo
from app.ui.shared import get_icon
from app.ui.shared.spinner import LoadingSpinner
from app.ui.overlay_window.hotkeys import HOTKEY_DESCRIPTIONS, DEFAULT_HOTKEYS

class AIConfigPanel(QFrame):
    def __init__(self, settings, theme_manager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.theme_manager = theme_manager
        self.setObjectName("aiConfigGroup")
        
        self.llm_config_collapsed = bool(self.settings.get("llm_config_collapsed", True))
        self.tema_modo = self.settings.get("tema_modo", "oscuro")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header Row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        self.llm_toggle_button = QPushButton("Configurar LLM:", self)
        self.llm_toggle_button.setObjectName("sectionToggle")
        self.llm_toggle_button.setToolTip("Mostrar/ocultar configuración del modelo de IA")
        self.llm_toggle_button.clicked.connect(self.toggle_llm_config)
        
        self.selector_temas = QComboBox(self)
        self.selector_temas.setObjectName("deviceCombo")
        self.selector_temas.setToolTip("Seleccionar tema visual de la interfaz")
        self.selector_temas.currentIndexChanged.connect(self._on_tema_selected)
        
        self.toggle_modo_btn = QPushButton(self)
        self.toggle_modo_btn.setObjectName("edgeButton")
        self.toggle_modo_btn.setIconSize(QSize(14, 14))
        self.toggle_modo_btn.setIcon(get_icon("moon"))
        self.toggle_modo_btn.setToolTip("Temas oscuros")
        self.toggle_modo_btn.clicked.connect(self.toggle_modo_tema)
        
        header_row.addWidget(self.llm_toggle_button, 0)
        header_row.addWidget(self.selector_temas, 0)
        header_row.addWidget(self.toggle_modo_btn, 0)
        header_row.addStretch(1)
        layout.addLayout(header_row)
        self._poblar_inicial()

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
        self.stt_provider_combo.setToolTip("Proveedor de transcripción de voz a texto")
        form_layout.addRow("STT Provider:", self.stt_provider_combo)

        self.whisper_model_combo = QComboBox(self)
        self.whisper_model_combo.addItems(["tiny", "base", "small"])
        self.whisper_model_combo.setToolTip("Modelo Whisper: tiny (rápido) → small (más preciso)")
        form_layout.addRow("Whisper Model:", self.whisper_model_combo)
        
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
        self.api_key_input.setToolTip("Clave API del proveedor seleccionado (no necesaria para LM Studio/Local)")
        form_layout.addRow("API Key:", self.api_key_input)

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
        form_layout.addRow("Model ID:", model_container)

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
        
        # --- Hotkey Config Section ---
        self.hotkey_config_collapsed = bool(self.settings.get("hotkey_config_collapsed", True))
        
        self.hotkey_toggle_button = QPushButton("Atajos de Teclado:", self)
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
            input_field = QLineEdit(self)
            input_field.setPlaceholderText(DEFAULT_HOTKEYS.get(action, ""))
            input_field.setToolTip(f"Formato: <modificador>+<tecla>\nEjemplo: <alt_gr>+g, <ctrl>+space")
            self.hotkey_inputs[action] = input_field
            hotkey_form.addRow(f"{description}:", input_field)
        
        hotkey_button_row = QHBoxLayout()
        self.reset_hotkeys_btn = QPushButton("Restaurar por defecto", self)
        self.reset_hotkeys_btn.setToolTip("Restaurar los atajos de teclado originales")
        self.reset_hotkeys_btn.clicked.connect(self._reset_hotkeys)
        self.hotkey_status_label = QLabel("", self)
        self.hotkey_status_label.setObjectName("statusLabel")
        hotkey_button_row.addWidget(self.hotkey_status_label, 1)
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
        self._apply_hotkey_config_visibility()
        self._aplicar_tema_inicial()

    def reload_icons(self):
        self.llm_toggle_button.setIcon(get_icon("expand") if self.llm_config_collapsed else get_icon("collapse"))
        self._actualizar_boton_modo()

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

    def _apply_hotkey_config_visibility(self):
        self.hotkey_config_body.setVisible(not self.hotkey_config_collapsed)
        self.hotkey_toggle_button.setIcon(get_icon("expand") if self.hotkey_config_collapsed else get_icon("collapse"))
        if self.parentWidget() and hasattr(self.parentWidget(), "adjustSize"):
            self.parentWidget().adjustSize()
        window = self.window()
        if window and hasattr(window, "adjustSize"):
            window.adjustSize()

    def _load_hotkey_settings(self):
        """Carga las hotkeys configuradas en los campos de entrada."""
        hotkeys = self.settings.get("hotkeys", {})
        for action, input_field in self.hotkey_inputs.items():
            current = hotkeys.get(action, DEFAULT_HOTKEYS.get(action, ""))
            input_field.setText(current)

    def _reset_hotkeys(self):
        """Restaura hotkeys por defecto."""
        for action, input_field in self.hotkey_inputs.items():
            input_field.setText(DEFAULT_HOTKEYS.get(action, ""))
        
        window = self.window()
        if window and hasattr(window, "hotkey_manager"):
            window.hotkey_manager.reset_hotkeys()
        
        self.hotkey_status_label.setText("Hotkeys restauradas!")
        QTimer.singleShot(2000, lambda: self.hotkey_status_label.setText(""))

    def toggle_modo_tema(self):
        orden = ["oscuro", "claro", "clasico"]
        idx = orden.index(self.tema_modo)
        self.tema_modo = orden[(idx + 1) % 3]
        self.settings.set("tema_modo", self.tema_modo)
        self._actualizar_boton_modo()
        self._repopulate_temas()

    def _actualizar_boton_modo(self):
        iconos = {"oscuro": "moon", "claro": "sun", "clasico": "dna"}
        tooltips = {"oscuro": "Temas oscuros", "claro": "Temas claros", "clasico": "Temas clásicos"}
        self.toggle_modo_btn.setIcon(get_icon(iconos[self.tema_modo]))
        self.toggle_modo_btn.setToolTip(tooltips[self.tema_modo])

    def _on_tema_selected(self, index):
        full_key = self.selector_temas.itemData(index)
        if full_key:
            self.theme_manager.cambiar_tema_interfaz(full_key)

    def _poblar_inicial(self):
        temas = filtrar_temas_por_modo(self.tema_modo)
        for display, full_key in temas:
            self.selector_temas.addItem(display, full_key)

    def _repopulate_temas(self):
        temas = filtrar_temas_por_modo(self.tema_modo)
        full_key_actual = self.selector_temas.currentData()
        self.selector_temas.blockSignals(True)
        self.selector_temas.clear()
        for display, full_key in temas:
            self.selector_temas.addItem(display, full_key)
        full_keys = [k for _, k in temas]
        if full_key_actual and full_key_actual in full_keys:
            self.selector_temas.setCurrentIndex(full_keys.index(full_key_actual))
            self.selector_temas.blockSignals(False)
        elif temas:
            self.selector_temas.setCurrentIndex(0)
            nuevo_tema = self.selector_temas.itemData(0)
            self.selector_temas.blockSignals(False)
            self.theme_manager.cambiar_tema_interfaz(nuevo_tema)
        else:
            self.selector_temas.blockSignals(False)

    def _aplicar_tema_inicial(self):
        tema_guardado = self.settings.get("tema", "Slate Minimalist (Clasico)")
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

    def _save_ai_settings(self):
        self.save_spinner.start()
        self.save_ai_button.setEnabled(False)
        self.save_ai_button.setText("Guardando...")
        self.ai_status_label.setText("Guardando...")

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
                self.ai_status_label.setText("Guardado!")
                get_llm_client().reload()
                window = self.window()
                if hasattr(window, "assistant"):
                    window.assistant.set_stt_settings(stt_provider, whisper_model)
            except OSError:
                self.ai_status_label.setText("Error!")
            finally:
                self.save_spinner.stop()
                self.save_ai_button.setEnabled(True)
                self.save_ai_button.setText("Guardar")

        # Guardar hotkeys también
        self._save_hotkey_settings()
        
        QTimer.singleShot(150, do_save)

    def _save_hotkey_settings(self):
        """Guarda las hotkeys configuradas."""
        hotkeys = {}
        for action, input_field in self.hotkey_inputs.items():
            value = input_field.text().strip()
            if value:
                hotkeys[action] = value
        
        self.settings.set("hotkeys", hotkeys)
        
        # Actualizar hotkey manager si existe
        window = self.window()
        if window and hasattr(window, "hotkey_manager"):
            for action, value in hotkeys.items():
                window.hotkey_manager.update_hotkey(action, value)
        
        self.hotkey_status_label.setText("Hotkeys guardadas!")
        QTimer.singleShot(2000, lambda: self.hotkey_status_label.setText(""))

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar modelo GGUF", "", "Modelos GGUF (*.gguf)"
        )
        if path:
            self.model_id_input.setText(path)

    def _download_model(self):
        self.download_model_btn.setEnabled(False)
        self.download_model_btn.setText("Descargando...")
        self.download_spinner.start()
        self.ai_status_label.setText("Descargando modelo (769 MB)...")
        QApplication.processEvents()

        from huggingface_hub import hf_hub_download
        from app.utils.path_utils import writable_models_dir

        model_dir = Path(writable_models_dir())
        dest = model_dir / "gemma-3-1b-it-Q4_K_M.gguf"

        try:
            hf_hub_download(
                repo_id="google/gemma-3-1b-it-GGUF",
                filename="gemma-3-1b-it-Q4_K_M.gguf",
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
                resume=True,
            )
            self.ai_status_label.setText("Descarga completada!")
            self.model_id_input.setText(str(dest))
            self.download_model_btn.setVisible(False)
        except Exception as e:
            self.ai_status_label.setText(f"Error: {e}")
        finally:
            self.download_model_btn.setEnabled(True)
            self.download_model_btn.setText("Descargar modelo")
            self.download_spinner.stop()
