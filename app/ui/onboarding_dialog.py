"""
Diálogo de onboarding para el primer lanzamiento de AYUDIN.
5 pasos: Introducción → Configurar LLM → Configurar STT → Atajos → ¡Listo!
Incluye formularios funcionales que guardan config.json directamente.
"""
import os
import json
import webbrowser
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QStackedWidget, QComboBox, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from app.ui.shared import get_icon, ui_settings
from app.ui.themes import obtener_qss, PALETAS
from app.utils.path_utils import writable_config_path
from app.ui.overlay_window.hotkeys import HOTKEY_DESCRIPTIONS, DEFAULT_HOTKEYS


TOTAL_STEPS = 5
TEMA_POR_DEFECTO = "Slate Minimalist (Clasico)"

LLM_PROVIDERS = {
    "google": "Google Gemini (gratis, en la nube)",
    "groq": "Groq (gratis, en la nube)",
    "lm_studio": "LM Studio (local, privado)",
    "local": "Local - llama.cpp (GPU/CPU, privado)",
}
CLOUD_PROVIDERS = {"google", "groq"}

GOOGLE_AI_STUDIO_URL = "https://aistudio.google.com/apikey"
GROQ_CONSOLE_URL = "https://console.groq.com/keys"


class OnboardingDialog(QDialog):
    """Diálogo de bienvenida con 5 pasos interactivos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bienvenido a AYUDIN")
        self.setMinimumSize(520, 460)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("onboardingDialog")
        self._current_step = 0
        self._tema_actual = ui_settings.get("tema", TEMA_POR_DEFECTO)

        # Cargar config existente para pre-llenar (si ya existe)
        self._load_existing_config()

        self._init_ui()
        self._aplicar_tema()

    def _load_existing_config(self):
        """Carga config.json existente para pre-llenar los formularios."""
        config_path = writable_config_path("config.json")
        self._existing_config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._existing_config = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    # ------------------------------------------------------------------
    # Tema / Estilo
    # ------------------------------------------------------------------

    def _aplicar_tema(self):
        """Aplica el QSS del tema actual al diálogo."""
        self.setStyleSheet(obtener_qss(self._tema_actual))

    def cambiar_tema_interfaz(self, nombre_tema: str):
        """Callback invocado por ThemeManager cuando cambia el tema."""
        self._tema_actual = nombre_tema
        self._aplicar_tema()

    # ------------------------------------------------------------------
    # UI Principal
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Título
        self.title_label = QLabel("Bienvenido a AYUDIN", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(17)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

        # Indicador de pasos
        self.step_indicator = QLabel("", self)
        self.step_indicator.setAlignment(Qt.AlignCenter)
        self.step_indicator.setObjectName("statusLabel")
        layout.addWidget(self.step_indicator)

        # Pasos (stacked)
        self.steps_stack = QStackedWidget(self)
        self.steps_stack.addWidget(self._create_intro())         # 0
        self.steps_stack.addWidget(self._create_llm_config())    # 1
        self.steps_stack.addWidget(self._create_stt_config())    # 2
        self.steps_stack.addWidget(self._create_hotkeys())       # 3
        self.steps_stack.addWidget(self._create_ready())         # 4
        layout.addWidget(self.steps_stack, 1)

        # Navegación
        nav_layout = QHBoxLayout()
        nav_layout.addStretch(1)

        self.prev_btn = QPushButton("← Anterior", self)
        self.prev_btn.clicked.connect(self._prev_step)
        self.prev_btn.setVisible(False)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Siguiente →", self)
        self.next_btn.clicked.connect(self._next_step)
        nav_layout.addWidget(self.next_btn)

        self.finish_btn = QPushButton("✓ Comenzar", self)
        self.finish_btn.setObjectName("saveButton")
        self.finish_btn.clicked.connect(self._finish)
        self.finish_btn.setVisible(False)
        nav_layout.addWidget(self.finish_btn)

        layout.addLayout(nav_layout)

        # Saltar
        skip_layout = QHBoxLayout()
        skip_layout.addStretch(1)
        self.skip_btn = QPushButton("Saltar guía", self)
        self.skip_btn.setObjectName("statusLabel")
        self.skip_btn.setFlat(True)
        self.skip_btn.clicked.connect(self.accept)
        skip_layout.addWidget(self.skip_btn)
        layout.addLayout(skip_layout)

        self._update_ui()

    # ------------------------------------------------------------------
    # Paso 1: Introducción
    # ------------------------------------------------------------------

    def _create_intro(self):
        w = self._make_step_widget("robot", "¿Qué es AYUDIN?")

        desc = QLabel(
            "AYUDIN es un asistente de escritorio que captura tu voz,\n"
            "la transcribe en tiempo real y la envía a una IA para\n"
            "generar respuestas inteligentes.\n\n"
            "<b>Flujo de trabajo:</b>\n"
            "  1️⃣  Hablas al micrófono (o capturas audio del sistema)\n"
            "  2️⃣  Tu voz se transcribe automáticamente\n"
            "  3️⃣  La transcripción se envía a un modelo de IA\n"
            "  4️⃣  La respuesta aparece en pantalla y en el visor de guiones\n\n"
            "En los siguientes pasos configuraremos el proveedor de IA,\n"
            "el reconocimiento de voz y los atajos de teclado.",
            w
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignLeft)
        w.layout().addWidget(desc)
        w.layout().addStretch()
        return w

    # ------------------------------------------------------------------
    # Paso 2: Configurar LLM
    # ------------------------------------------------------------------

    def _create_llm_config(self):
        w = self._make_step_widget("sun", "Configurar Proveedor de IA (LLM)")

        form = QFormLayout()
        form.setSpacing(10)

        # Provider combo
        self.llm_provider_combo = QComboBox(w)
        for key, label in LLM_PROVIDERS.items():
            self.llm_provider_combo.addItem(label, key)

        existing_provider = self._existing_config.get("provider", "google")
        idx = self.llm_provider_combo.findData(existing_provider)
        if idx >= 0:
            self.llm_provider_combo.setCurrentIndex(idx)

        self.llm_provider_combo.currentIndexChanged.connect(self._on_llm_provider_changed)
        self.llm_provider_combo.setToolTip("Elige qué IA quieres usar")
        form.addRow("Proveedor:", self.llm_provider_combo)

        # API Key input
        self.api_key_input = QLineEdit(w)
        self.api_key_input.setPlaceholderText("Pega tu API key aquí...")
        self.api_key_input.setText(self._existing_config.get("api_key", ""))
        self.api_key_input.setToolTip("API key del proveedor seleccionado")
        form.addRow("API Key:", self.api_key_input)

        # Link para obtener API key (QPushButton estilizado como link)
        self.api_link_btn = QPushButton("", w)
        self.api_link_btn.setObjectName("linkButton")
        self.api_link_btn.setCursor(Qt.PointingHandCursor)
        self.api_link_btn.setToolTip("Abrir en el navegador")
        self.api_link_btn.clicked.connect(self._abrir_link_api_key)
        form.addRow("", self.api_link_btn)

        # Instrucciones
        self.llm_instructions = QLabel("", w)
        self.llm_instructions.setWordWrap(True)
        self.llm_instructions.setAlignment(Qt.AlignLeft)
        form.addRow("", self.llm_instructions)

        w.layout().addLayout(form)

        # Visibilidad inicial según el proveedor
        self._apply_llm_provider_visibility()
        w.layout().addStretch()
        return w

    def _on_llm_provider_changed(self):
        self._apply_llm_provider_visibility()

    def _apply_llm_provider_visibility(self):
        provider_key = self.llm_provider_combo.currentData()
        is_cloud = provider_key in CLOUD_PROVIDERS

        self.api_key_input.setVisible(is_cloud)
        self.api_link_btn.setVisible(is_cloud)
        self.llm_instructions.setVisible(is_cloud)

        if is_cloud and provider_key == "google":
            self.api_link_btn.setText("Obtener API key en Google AI Studio →")
            self.llm_instructions.setText(
                "<b>¿Cómo obtener una API key de Google?</b>\n"
                "1. Haz clic en el enlace de arriba\n"
                "2. Inicia sesión con tu cuenta de Google\n"
                "3. Haz clic en 'Create API Key'\n"
                "4. Copia la clave y pégala aquí\n\n"
                "Es <b>gratuita</b> y no requiere tarjeta de crédito."
            )
            self.api_key_input.setPlaceholderText("Pega tu API key de Google aquí...")
        elif is_cloud and provider_key == "groq":
            self.api_link_btn.setText("Obtener API key en Groq Console →")
            self.llm_instructions.setText(
                "<b>¿Cómo obtener una API key de Groq?</b>\n"
                "1. Haz clic en el enlace de arriba\n"
                "2. Crea una cuenta gratuita\n"
                "3. Ve a 'API Keys' y genera una nueva\n"
                "4. Copia la clave y pégala aquí\n\n"
                "Groq ofrece acceso gratuito a modelos rápidos."
            )
            self.api_key_input.setPlaceholderText("Pega tu API key de Groq aquí...")

    def _abrir_link_api_key(self):
        """Abre la URL correcta según el proveedor seleccionado."""
        provider_key = self.llm_provider_combo.currentData()
        if provider_key == "google":
            webbrowser.open(GOOGLE_AI_STUDIO_URL)
        elif provider_key == "groq":
            webbrowser.open(GROQ_CONSOLE_URL)

    # ------------------------------------------------------------------
    # Paso 3: Configurar STT
    # ------------------------------------------------------------------

    def _create_stt_config(self):
        w = self._make_step_widget("mic", "Configurar Reconocimiento de Voz (STT)")

        desc = QLabel(
            "Elige cómo quieres que AYUDIN transcriba tu voz:\n\n"
            "<b>Google (Nube):</b> Más preciso, requiere internet y API key.\n"
            "<b>Local (faster-whisper):</b> Funciona sin internet, privado,\n"
            "pero requiere descargar un modelo (el primero se descarga solo).",
            w
        )
        desc.setWordWrap(True)
        w.layout().addWidget(desc)

        form = QFormLayout()
        form.setSpacing(10)

        self.stt_provider_combo = QComboBox(w)
        self.stt_provider_combo.addItem("Google (Nube)", "google")
        self.stt_provider_combo.addItem("Local (faster-whisper)", "whisper")
        self.stt_provider_combo.setToolTip(
            "Google: más preciso, requiere internet\nLocal: privado, sin internet"
        )

        existing_stt = self._existing_config.get("stt_provider", "google")
        idx = self.stt_provider_combo.findData(existing_stt)
        if idx >= 0:
            self.stt_provider_combo.setCurrentIndex(idx)

        form.addRow("Proveedor STT:", self.stt_provider_combo)
        w.layout().addLayout(form)
        w.layout().addStretch()
        return w

    # ------------------------------------------------------------------
    # Paso 4: Atajos de Teclado
    # ------------------------------------------------------------------

    def _create_hotkeys(self):
        w = self._make_step_widget("expand", "Atajos de Teclado Globales")

        desc = QLabel(
            "AYUDIN tiene atajos globales que funcionan desde <b>cualquier</b>\n"
            "aplicación, incluso cuando la ventana no está enfocada:",
            w
        )
        desc.setWordWrap(True)
        w.layout().addWidget(desc)

        for action, description in HOTKEY_DESCRIPTIONS.items():
            hotkey = DEFAULT_HOTKEYS.get(action, "")
            row = QLabel(f"  <b>{hotkey}</b>  →  {description}", w)
            row.setObjectName("statusLabel")
            w.layout().addWidget(row)

        tip = QLabel(
            "\nEstos atajos se pueden personalizar después en el panel\n"
            "de configuración (sección 'Atajos de Teclado').",
            w
        )
        tip.setWordWrap(True)
        w.layout().addWidget(tip)

        w.layout().addStretch()
        return w

    # ------------------------------------------------------------------
    # Paso 5: ¡Listo!
    # ------------------------------------------------------------------

    def _create_ready(self):
        w = self._make_step_widget("dna", "¡Todo listo!")

        self.ready_summary = QLabel("", w)
        self.ready_summary.setWordWrap(True)
        self.ready_summary.setAlignment(Qt.AlignLeft)
        w.layout().addWidget(self.ready_summary)

        final = QLabel(
            "\nPuedes cambiar cualquier configuración después desde\n"
            "el panel de configuración de la ventana principal.\n\n"
            "Presiona <b>AltGr+G</b> para empezar a grabar. ¡A disfrutar!",
            w
        )
        final.setWordWrap(True)
        w.layout().addWidget(final)

        w.layout().addStretch()
        return w

    # ------------------------------------------------------------------
    # Helpers de UI
    # ------------------------------------------------------------------

    def _make_step_widget(self, icon_name: str, title: str) -> QWidget:
        """Crea un widget base con ícono + título para un paso."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 4, 8, 4)

        icon_label = QLabel()
        icon_label.setPixmap(get_icon(icon_name).pixmap(44, 44))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title, widget)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("sectionLabel")
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        return widget

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------

    def _next_step(self):
        if self._current_step < TOTAL_STEPS - 1:
            self._current_step += 1
            self.steps_stack.setCurrentIndex(self._current_step)
            self._update_ui()
            if self._current_step == TOTAL_STEPS - 1:
                self._update_ready_summary()

    def _prev_step(self):
        if self._current_step > 0:
            self._current_step -= 1
            self.steps_stack.setCurrentIndex(self._current_step)
            self._update_ui()

    def _update_ui(self):
        self.step_indicator.setText(f"Paso {self._current_step + 1} de {TOTAL_STEPS}")
        self.prev_btn.setVisible(self._current_step > 0)
        self.next_btn.setVisible(self._current_step < TOTAL_STEPS - 1)
        self.finish_btn.setVisible(self._current_step == TOTAL_STEPS - 1)

    def _update_ready_summary(self):
        """Actualiza el resumen del último paso con la configuración elegida."""
        provider_label = self.llm_provider_combo.currentText()
        stt_label = self.stt_provider_combo.currentText()
        has_api_key = bool(self.api_key_input.text().strip())

        summary = (
            "<b>Tu configuración:</b>\n\n"
            f"  🔹 IA: {provider_label}\n"
        )
        if has_api_key:
            summary += "  🔹 API Key: Configurada ✓\n"
        else:
            summary += "  🔹 API Key: Sin configurar (puedes agregarla después)\n"
        summary += f"  🔹 Voz: {stt_label}\n"
        summary += "  🔹 Atajos: AltGr+G, AltGr+\\, AltGr+H"

        self.ready_summary.setText(summary)

    # ------------------------------------------------------------------
    # Guardar configuración
    # ------------------------------------------------------------------

    def _finish(self):
        """Guarda la configuración y cierra."""
        self._save_config()
        self.accept()

    def _save_config(self):
        """Escribe config.json con las opciones del onboarding y recarga clientes."""
        from app.core.llm_client import get_llm_client

        config_path = writable_config_path("config.json")
        folder = os.path.dirname(config_path)
        os.makedirs(folder, exist_ok=True)

        stt_provider = self.stt_provider_combo.currentData()
        llm_provider = self.llm_provider_combo.currentData()
        api_key = self.api_key_input.text().strip()

        config = {
            "stt_provider": stt_provider,
            "whisper_model": self._existing_config.get("whisper_model", "tiny"),
            "provider": llm_provider,
            "api_key": api_key,
            "model_id": self._existing_config.get("model_id", ""),
        }

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"Onboarding: configuración guardada en {config_path}")
        except OSError as e:
            print(f"Onboarding: error al guardar configuración: {e}")
            return

        # Recargar LLM client y actualizar STT del asistente
        try:
            get_llm_client().reload()
        except Exception as e:
            print(f"Onboarding: error al recargar LLM client: {e}")

        parent = self.parentWidget()
        if parent and hasattr(parent, "assistant"):
            try:
                parent.assistant.set_stt_settings(stt_provider,
                    self._existing_config.get("whisper_model", "tiny"))
            except Exception as e:
                print(f"Onboarding: error al actualizar STT: {e}")

    # ------------------------------------------------------------------
    # Eventos de teclado
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()  # Cerrar sin guardar (solo "Comenzar" guarda)
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self._current_step < TOTAL_STEPS - 1:
                self._next_step()
            else:
                self._finish()
        else:
            super().keyPressEvent(event)
