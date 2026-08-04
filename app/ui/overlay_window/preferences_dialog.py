"""
Diálogo de preferencias no-modal: edición de IA, apariencia y atajos,
con sidebar de navegación estilo panel de preferencias moderno.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QScrollArea, QSizePolicy, QButtonGroup
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QIcon

from app.ui.shared import ui_settings, DragMixin, get_icon
from app.ui.shared.icons import get_logo_pixmap
from app.ui.themes import PALETAS, obtener_qss, normalizar_tema
from app.ui.overlay_window.ai_config import AIConfigPanel


class PreferencesDialog(DragMixin, QWidget):
    def __init__(self, settings, theme_manager, overlay, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferencias de HelPy")
        self.setObjectName("preferencesDialog")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(620)
        self.setMaximumWidth(780)

        self.setWindowIcon(QIcon(get_logo_pixmap(64, 64)))

        self.panel = AIConfigPanel(settings, theme_manager, overlay, self)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(6)

        # Header row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(6, 4, 6, 0)

        self.logo_label = QLabel(self)
        self.logo_label.setPixmap(get_logo_pixmap(38, 20))
        self.logo_label.setFixedHeight(20)
        header_row.addWidget(self.logo_label)

        self.title_label = QLabel("Preferencias de HelPy", self)
        self.title_label.setObjectName("appTitle")
        header_row.addWidget(self.title_label)
        header_row.addStretch(1)

        self.close_btn = QPushButton(self)
        self.close_btn.setObjectName("edgeButton")
        self.close_btn.setIcon(get_icon("close"))
        self.close_btn.setIconSize(QSize(14, 14))
        self.close_btn.setToolTip("Cerrar las preferencias")
        self.close_btn.clicked.connect(self.close)
        header_row.addWidget(self.close_btn)
        outer.addLayout(header_row)

        # Main container
        self.container = QFrame(self)
        self.container.setObjectName("overlayContainer")
        self.container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)

        body_layout = QHBoxLayout(self.container)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame(self)
        sidebar.setObjectName("preferencesSidebar")
        sidebar.setFixedWidth(172)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        sidebar_layout.setSpacing(4)

        sidebar_title = QLabel("Secciones", self)
        sidebar_title.setObjectName("statusLabel")
        sidebar_title.setStyleSheet("padding: 4px 8px 8px 8px; font-weight: bold;")
        sidebar_layout.addWidget(sidebar_title)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        nav_items = [
            ("ia",          "Inteligencia\nArtificial"),
            ("apariencia",  "Apariencia"),
            ("atajos",      "Atajos de\nteclado"),
        ]

        self._nav_buttons = {}

        def _make_handler(k):
            return lambda checked: self._switch_section(k)

        for i, (key, label) in enumerate(nav_items):
            btn = QPushButton(label, self)
            btn.setObjectName("preferencesNavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(36)
            btn.clicked.connect(_make_handler(key))
            self._nav_group.addButton(btn, i)
            sidebar_layout.addWidget(btn)
            self._nav_buttons[key] = btn

        sidebar_layout.addStretch(1)

        self.reonboard_btn = QPushButton("Reiniciar guía", self)
        self.reonboard_btn.setObjectName("preferencesNavButton")
        self.reonboard_btn.setCursor(Qt.PointingHandCursor)
        self.reonboard_btn.setToolTip("Volver a mostrar la guía de inicio paso a paso")
        self.reonboard_btn.clicked.connect(self._reopen_onboarding)
        sidebar_layout.addWidget(self.reonboard_btn)

        self._nav_buttons["ia"].setChecked(True)

        body_layout.addWidget(sidebar)

        # Content area
        content = QFrame(self)
        content.setObjectName("preferencesContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 17, 16, 12)
        content_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName("preferencesContent")
        scroll.setStyleSheet("background: transparent;")
        scroll.viewport().setAutoFillBackground(False)
        scroll.viewport().setStyleSheet("background: transparent;")
        self._scroll_widget = QWidget(self)
        self._scroll_widget.setObjectName("scrollWidget")
        self._scroll_widget.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(self._scroll_widget)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(0)
        self._scroll_layout.addWidget(self.panel)
        self._scroll_layout.addStretch(1)
        scroll.setWidget(self._scroll_widget)
        content_layout.addWidget(scroll)

        body_layout.addWidget(content)

        outer.addWidget(self.container)

        self._hide_section_toggles()
        self._switch_section("ia")

        self._apply_theme()
        self.resize(680, 520)

    def _hide_section_toggles(self):
        """Oculta los botones de colapsar sección: la sidebar ya navega."""
        self.panel.llm_toggle_button.setVisible(False)
        self.panel.apariencia_toggle_button.setVisible(False)
        self.panel.hotkey_toggle_button.setVisible(False)
        self.panel.ai_config_body.setVisible(True)
        self.panel.apariencia_config_body.setVisible(True)
        self.panel.hotkey_config_body.setVisible(True)

    def _switch_section(self, key: str):
        sections = {
            "ia":         self.panel.ai_config_body,
            "apariencia": self.panel.apariencia_config_body,
            "atajos":     self.panel.hotkey_config_body,
        }
        for k, widget in sections.items():
            widget.setVisible(k == key)

    def _apply_theme(self):
        tema = normalizar_tema(self.panel.settings.get("tema", "Slate Minimalist (Clásico)"))
        self.setStyleSheet(obtener_qss(tema))

    def cambiar_tema_interfaz(self, nombre_tema):
        """Lo llama ThemeManager al cambiar de tema: repinta el diálogo."""
        if not hasattr(self, "panel"):
            return
        nombre_tema = normalizar_tema(nombre_tema)
        self.setStyleSheet(obtener_qss(nombre_tema))
        theme_data = PALETAS.get(nombre_tema, PALETAS["Slate Minimalist (Clásico)"])
        color = QColor(theme_data["resaltado"])
        for attr in ("save_spinner", "download_spinner"):
            spinner = getattr(self.panel, attr, None)
            if spinner is not None:
                spinner.set_color(color)

    def reload_icons(self):
        self.close_btn.setIcon(get_icon("close"))
        if hasattr(self.panel, "reload_icons"):
            self.panel.reload_icons()

    def show_preferences(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _reopen_onboarding(self):
        """Reinicia la guía de inicio y la abre de nuevo."""
        ui_settings.set("onboarding_completed", False)
        overlay = self.panel._overlay if hasattr(self.panel, "_overlay") else None
        if overlay and hasattr(overlay, "_show_onboarding"):
            self.close()
            overlay._show_onboarding()
