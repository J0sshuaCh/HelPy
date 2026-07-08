"""
Diálogo de onboarding para el primer lanzamiento de HelPy.
5 pasos: Introducción → Configurar LLM → Configurar STT → Atajos → ¡Listo!
Incluye formularios funcionales que guardan config.json directamente.
"""
import os
import json
import webbrowser
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QStackedWidget, QComboBox, QLineEdit, QFormLayout,
    QDesktopWidget, QFrame
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
    "google": "Google Gemini  (gratis, en la nube)",
    "groq": "Groq  (gratis, en la nube)",
    "lm_studio": "LM Studio  (local, sin internet)",
    "local": "llama.cpp  (local, GPU/CPU)",
}
CLOUD_PROVIDERS = {"google", "groq"}

GOOGLE_AI_STUDIO_URL = "https://aistudio.google.com/apikey"
GROQ_CONSOLE_URL = "https://console.groq.com/keys"
LM_STUDIO_URL = "https://lmstudio.ai/"
HUGGINGFACE_GGUF_URL = "https://huggingface.co/models?search=gguf"

LINK_URLS = {
    "google": GOOGLE_AI_STUDIO_URL,
    "groq": GROQ_CONSOLE_URL,
    "lm_studio": LM_STUDIO_URL,
    "local": HUGGINGFACE_GGUF_URL,
}

SEPARATOR = (
    '<hr style="border: none; border-top: 1px solid %s; margin: 8px 0;">'
)


class OnboardingDialog(QDialog):
    """Diálogo de bienvenida con 5 pasos interactivos."""

    def __init__(self, parent=None):
        super().__init__(None)
        self._overlay_window = parent  # guardado aparte, no como parent Qt
        self.setWindowTitle("Bienvenido a HelPy")
        self.setMinimumSize(520, 400)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        from app.ui.shared.icons import get_color_logo_icon
        self.setWindowIcon(get_color_logo_icon(64))
        self.setObjectName("onboardingDialog")
        self._current_step = 0
        self._tema_actual = ui_settings.get("tema", TEMA_POR_DEFECTO)

        self._load_existing_config()
        self._init_ui()
        self._aplicar_tema()
        self._center_on_screen()

    def _load_existing_config(self):
        config_path = writable_config_path("config.json")
        self._existing_config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._existing_config = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    # ------------------------------------------------------------------
    # Tema y posición
    # ------------------------------------------------------------------

    def _aplicar_tema(self):
        self.setStyleSheet(obtener_qss(self._tema_actual))
        # Actualizar logo según tema
        if hasattr(self, 'title_label'):
            from app.ui.shared.icons import get_logo_pixmap
            self.title_label.setPixmap(get_logo_pixmap(200, 110))

    def cambiar_tema_interfaz(self, nombre_tema: str):
        self._tema_actual = nombre_tema
        self._aplicar_tema()

    def _center_on_screen(self):
        geom = self.frameGeometry()
        center = QDesktopWidget().availableGeometry().center()
        geom.moveCenter(center)
        self.move(geom.topLeft())

    # ------------------------------------------------------------------
    # UI Principal
    # ------------------------------------------------------------------

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 14, 22, 12)
        layout.setSpacing(6)

        self.title_label = QLabel(self)
        from app.ui.shared.icons import get_logo_pixmap
        self.title_label.setPixmap(get_logo_pixmap(200, 110))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.step_indicator = QLabel("", self)
        self.step_indicator.setAlignment(Qt.AlignCenter)
        self.step_indicator.setObjectName("statusLabel")
        layout.addWidget(self.step_indicator)

        self.steps_stack = QStackedWidget(self)
        self.steps_stack.addWidget(self._create_intro())         # 0
        self.steps_stack.addWidget(self._create_llm_config())    # 1
        self.steps_stack.addWidget(self._create_stt_config())    # 2
        self.steps_stack.addWidget(self._create_hotkeys())       # 3
        self.steps_stack.addWidget(self._create_ready())         # 4
        layout.addWidget(self.steps_stack)
        
        # Espacio mínimo entre contenido y botones
        layout.addSpacing(4)

        # Navegación
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        nav_layout.addStretch(1)

        self.prev_btn = QPushButton("← Atrás", self)
        self.prev_btn.clicked.connect(self._prev_step)
        self.prev_btn.setVisible(False)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Siguiente →", self)
        self.next_btn.clicked.connect(self._next_step)
        nav_layout.addWidget(self.next_btn)

        self.finish_btn = QPushButton("✓   Comenzar", self)
        self.finish_btn.setObjectName("saveButton")
        self.finish_btn.clicked.connect(self._finish)
        self.finish_btn.setVisible(False)
        nav_layout.addWidget(self.finish_btn)

        layout.addLayout(nav_layout)

        skip_layout = QHBoxLayout()
        skip_layout.addStretch(1)
        self.skip_btn = QPushButton("Saltar guía", self)
        self.skip_btn.setObjectName("linkButton")
        self.skip_btn.setFlat(True)
        self.skip_btn.clicked.connect(self.accept)
        skip_layout.addWidget(self.skip_btn)
        layout.addLayout(skip_layout)

        self._update_ui()

    # ------------------------------------------------------------------
    # Paso 1: Introducción
    # ------------------------------------------------------------------

    def _create_intro(self):
        w = self._make_step_widget("monitor", "¿Qué es HelPy?")

        desc = QLabel(
            "Un asistente de escritorio que escucha tu voz, la convierte\n"
            "en texto y la envía a inteligencia artificial para obtener\n"
            "respuestas al instante.",
            w
        )
        desc.setWordWrap(True)
        w.layout().addWidget(desc)

        sub = QLabel("¿Cómo funciona?", w)
        sub.setObjectName("sectionLabel")
        sub.setWordWrap(True)
        w.layout().addWidget(sub)

        steps = QLabel(
            "  🎤  Hablas o capturas audio del sistema\n"
            "  📝  Tu voz se transcribe en tiempo real\n"
            "  🧠  La IA procesa el texto y genera una respuesta\n"
            "  💬  El resultado aparece en pantalla",
            w
        )
        steps.setWordWrap(True)
        w.layout().addWidget(steps)

        final = QLabel("Vamos a configurarlo en menos de un minuto.", w)
        final.setWordWrap(True)
        w.layout().addWidget(final)

        return w

    # ------------------------------------------------------------------
    # Paso 2: Configurar LLM
    # ------------------------------------------------------------------

    def _create_llm_config(self):
        w = self._make_step_widget("sun", "Elige tu proveedor de IA")

        form = QFormLayout()
        form.setSpacing(8)

        self.llm_provider_combo = QComboBox(w)
        for key, label in LLM_PROVIDERS.items():
            self.llm_provider_combo.addItem(label, key)

        existing_provider = self._existing_config.get("provider", "google")
        idx = self.llm_provider_combo.findData(existing_provider)
        if idx >= 0:
            self.llm_provider_combo.setCurrentIndex(idx)

        self.llm_provider_combo.currentIndexChanged.connect(
            self._on_llm_provider_changed
        )
        form.addRow("Proveedor:", self.llm_provider_combo)

        self.api_key_input = QLineEdit(w)
        self.api_key_input.setPlaceholderText("Pega tu API key aquí...")
        self.api_key_input.setText(self._existing_config.get("api_key", ""))
        form.addRow("API Key:", self.api_key_input)

        self.api_link_btn = QPushButton("", w)
        self.api_link_btn.setObjectName("linkButton")
        self.api_link_btn.setCursor(Qt.PointingHandCursor)
        self.api_link_btn.clicked.connect(self._abrir_link)
        form.addRow("", self.api_link_btn)

        self.llm_instructions = QLabel("", w)
        self.llm_instructions.setWordWrap(True)
        self.llm_instructions.setAlignment(Qt.AlignLeft)
        form.addRow("", self.llm_instructions)

        w.layout().addLayout(form)
        self._apply_llm_provider_visibility()
        return w

    def _on_llm_provider_changed(self):
        self._apply_llm_provider_visibility()

    def _apply_llm_provider_visibility(self):
        key = self.llm_provider_combo.currentData()
        is_cloud = key in CLOUD_PROVIDERS

        self.api_key_input.setVisible(is_cloud)
        self.api_link_btn.setVisible(True)
        self.llm_instructions.setVisible(True)

        if key == "google":
            self.api_link_btn.setText("Ir a Google AI Studio →")
            self.llm_instructions.setText(
                "<b>¿No tienes API key?</b>\n\n"
                "  1.  Arriba abre Google AI Studio\n"
                "  2.  Inicia sesión con tu cuenta Google\n"
                "  3.  Pulsa <b>Create API Key</b>\n"
                "  4.  Copia y pega la clave arriba\n\n"
                "Gratis, sin tarjeta de crédito."
            )
            self.api_key_input.setPlaceholderText("AIz... tu key de Google")

        elif key == "groq":
            self.api_link_btn.setText("Ir a Groq Console →")
            self.llm_instructions.setText(
                "<b>¿No tienes API key?</b>\n\n"
                "  1.  Arriba abre Groq Console\n"
                "  2.  Crea una cuenta gratuita\n"
                "  3.  Ve a <b>API Keys</b> y genera una\n"
                "  4.  Copia y pega la clave arriba\n\n"
                "Acceso gratuito a modelos rápidos."
            )
            self.api_key_input.setPlaceholderText("gsk_... tu key de Groq")

        elif key == "lm_studio":
            self.api_link_btn.setText("Descargar LM Studio →")
            self.llm_instructions.setText(
                "<b>LM Studio corre en tu PC, sin internet.</b>\n"
                "No necesitas API key.\n\n"
                "  1.  Descarga LM Studio del enlace\n"
                "  2.  Instálalo y busca un modelo\n"
                "  3.  Ve a la pestaña <b>Developer</b>\n"
                "  4.  Activa <b>Start Server</b>\n\n"
                "HelPy se conecta automáticamente."
            )

        elif key == "local":
            self.api_link_btn.setText("Buscar modelos GGUF →")
            self.llm_instructions.setText(
                "<b>llama.cpp carga modelos locales.</b>\n"
                "No necesitas API key ni internet.\n\n"
                "  1.  Descarga un modelo .gguf del enlace\n"
                "  2.  Recomendado: gemma-3-1b-it (ligero)\n"
                "  3.  En Configurar LLM selecciona el archivo\n\n"
                "También puedes usar el botón Descargar Modelo\n"
                "en la configuración avanzada."
            )

    def _abrir_link(self):
        key = self.llm_provider_combo.currentData()
        url = LINK_URLS.get(key)
        if url:
            webbrowser.open(url)

    # ------------------------------------------------------------------
    # Paso 3: Configurar STT
    # ------------------------------------------------------------------

    def _create_stt_config(self):
        w = self._make_step_widget("mic", "Reconocimiento de voz")

        form = QFormLayout()
        form.setSpacing(8)

        self.stt_provider_combo = QComboBox(w)
        self.stt_provider_combo.addItem("Google Cloud  (preciso, con internet)", "google")
        self.stt_provider_combo.addItem("faster-whisper  (local, sin internet)", "whisper")

        existing_stt = self._existing_config.get("stt_provider", "google")
        idx = self.stt_provider_combo.findData(existing_stt)
        if idx >= 0:
            self.stt_provider_combo.setCurrentIndex(idx)

        form.addRow("Motor:", self.stt_provider_combo)
        w.layout().addLayout(form)

        desc = QLabel(
            "<br><b>Google Cloud</b> — más preciso, necesita internet<br>"
            "     y usa la misma API key que configuraste antes.\n\n"
            "<b>faster-whisper</b> — privado, sin internet. Descarga\n"
            "     automáticamente el modelo la primera vez (~75 MB).",
            w
        )
        desc.setWordWrap(True)
        w.layout().addWidget(desc)
        return w

    # ------------------------------------------------------------------
    # Paso 4: Atajos de Teclado
    # ------------------------------------------------------------------

    def _create_hotkeys(self):
        w = self._make_step_widget("expand", "Atajos globales")

        desc = QLabel(
            "Funcionan en <b>cualquier aplicación</b>, sin enfocar HelPy:",
            w
        )
        desc.setWordWrap(True)
        w.layout().addWidget(desc)

        # Hotkey table
        table = QFrame(w)
        table_layout = QVBoxLayout(table)
        table_layout.setSpacing(8)
        table_layout.setContentsMargins(0, 8, 0, 8)

        for action, description in HOTKEY_DESCRIPTIONS.items():
            hotkey = DEFAULT_HOTKEYS.get(action, "")
            row = QHBoxLayout()
            key_label = QLabel(hotkey)
            key_label.setObjectName("sectionLabel")
            key_label.setMinimumWidth(90)
            row.addWidget(key_label)
            desc_label = QLabel(description)
            desc_label.setObjectName("statusLabel")
            row.addWidget(desc_label, 1)
            table_layout.addLayout(row)

        w.layout().addWidget(table)

        tip = QLabel(
            "Puedes cambiarlos después en Configuración → Atajos de Teclado.",
            w
        )
        tip.setWordWrap(True)
        w.layout().addWidget(tip)
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
            "\nPresiona <b>AltGr + G</b> para empezar a grabar.\n"
            "Cambia cualquier ajuste desde el panel de configuración.\n\n"
            "¡A disfrutar! 🚀",
            w
        )
        final.setWordWrap(True)
        w.layout().addWidget(final)
        return w

    # ------------------------------------------------------------------
    # Helpers de UI
    # ------------------------------------------------------------------

    def _make_step_widget(self, icon_name: str, title: str) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 0, 8, 0)

        icon_label = QLabel()
        icon_label.setPixmap(get_icon(icon_name).pixmap(28, 28))
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
        llm_label = self.llm_provider_combo.currentText()
        stt_label = self.stt_provider_combo.currentText()
        has_key = bool(self.api_key_input.text().strip())

        lines = ["<b>Tu configuración:</b><br>", f"  IA: {llm_label}"]
        if has_key:
            lines.append("  API Key: configurada ✓")
        else:
            lines.append("  API Key: (sin configurar)")
        lines.append(f"  Voz: {stt_label}")
        lines.append("  Atajos: AltGr+G, AltGr+\\, AltGr+H")

        self.ready_summary.setText("<br>".join(lines))

    # ------------------------------------------------------------------
    # Guardar configuración
    # ------------------------------------------------------------------

    def _finish(self):
        self._save_config()
        self.accept()

    def _save_config(self):
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
        except OSError as e:
            print(f"Onboarding: error al guardar configuración: {e}")
            return

        try:
            get_llm_client().reload()
        except Exception as e:
            print(f"Onboarding: error al recargar LLM client: {e}")

        if self._overlay_window and hasattr(self._overlay_window, "assistant"):
            try:
                self._overlay_window.assistant.set_stt_settings(
                    stt_provider,
                    self._existing_config.get("whisper_model", "tiny"),
                )
            except Exception as e:
                print(f"Onboarding: error al actualizar STT: {e}")

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self._current_step < TOTAL_STEPS - 1:
                self._next_step()
            else:
                self._finish()
        else:
            super().keyPressEvent(event)
