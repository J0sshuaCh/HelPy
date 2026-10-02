from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt5.QtCore import QSize
from app.ui.shared import get_icon
from app.ui.shared.icons import get_logo_pixmap
from app.ui.shared.recording_indicator import RecordingIndicator
from app.ui.shared.hotkeys_display import get_hotkey_display

class HeaderArea(QFrame):
    def __init__(self, title="HelPy", parent=None):
        super().__init__(parent)
        self.setObjectName("headerArea")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 2)
        self.layout.setSpacing(5)
        
        self.logo_label = QLabel()
        self.logo_label.setPixmap(get_logo_pixmap(38, 20))
        self.logo_label.setFixedHeight(20)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("appTitle")
        
        self.capture_button = QPushButton("", self)
        self.capture_button.setObjectName("edgeButton")
        self.capture_button.setIcon(get_icon("eye_off"))
        self.capture_button.setIconSize(QSize(14, 14))
        self.capture_button.setToolTip("Mostrar/ocultar ventana en capturas de pantalla")
        self.capture_button.setAccessibleName("Visibilidad en captura de pantalla")
        
        self.compact_button = QPushButton("", self)
        self.compact_button.setObjectName("edgeButton")
        self.compact_button.setCheckable(True)
        self.compact_button.setIcon(get_icon("panels"))
        self.compact_button.setIconSize(QSize(14, 14))
        self.compact_button.setToolTip("Modo compacto/expandido\nAlterna mostrar todo o solo respuesta")
        self.compact_button.setAccessibleName("Alternar modo compacto")

        self.settings_button = QPushButton("", self)
        self.settings_button.setObjectName("edgeButton")
        self.settings_button.setIcon(get_icon("settings"))
        self.settings_button.setIconSize(QSize(14, 14))
        self.settings_button.setToolTip("Abrir las preferencias")
        self.settings_button.setAccessibleName("Abrir preferencias de configuración")
        
        self.edge_button = QPushButton("", self)
        self.edge_button.setObjectName("edgeButton")
        self.edge_button.setIcon(get_icon("collapse"))
        self.edge_button.setIconSize(QSize(14, 14))
        self.edge_button.setToolTip(self._edge_tooltip())
        self.edge_button.setAccessibleName("Colapsar o expandir ventana")
        
        self.layout.addWidget(self.logo_label)
        self.layout.addWidget(self.title_label)
        self.layout.addStretch(1)

        self.recording_indicator = RecordingIndicator(self)
        self.layout.addWidget(self.recording_indicator)

        self.hotkey_chip = QLabel(self)
        self.hotkey_chip.setObjectName("hotkeyChip")
        self.hotkey_chip.setToolTip("Atajo para iniciar/detener la grabación")
        self._update_hotkey_chip()
        self.layout.addWidget(self.hotkey_chip)

        self.layout.addWidget(self.capture_button)
        self.layout.addWidget(self.compact_button)
        self.layout.addWidget(self.settings_button)
        self.layout.addWidget(self.edge_button)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(self.sizeHint().height())

    def set_recording(self, active: bool):
        self.recording_indicator.set_recording(active)

    def refresh_icons(self):
        """Recarga todos los iconos (tras cambio de tema)."""
        is_cap_visible = getattr(self.parent(), "capture_visible", False)
        self.capture_button.setIcon(get_icon("eye" if is_cap_visible else "eye_off"))
        self.compact_button.setIcon(get_icon("panels"))
        self.settings_button.setIcon(get_icon("settings"))
        icon_name = "expand" if getattr(self.parent(), "is_collapsed", False) else "collapse"
        self.edge_button.setIcon(get_icon(icon_name))

    def _edge_tooltip(self, collapsed=None):
        hint = get_hotkey_display("toggle_collapse")
        if collapsed is None:
            base = "Colapsar/expandir panel"
        else:
            base = "Expandir panel" if collapsed else "Colapsar panel"
        return base + (f"\nAtajo: {hint}" if hint else "")

    def refresh_hotkey_tooltips(self):
        """Actualiza los tooltips con las hotkeys actuales para que no mientan tras remapear."""
        self.edge_button.setToolTip(self._edge_tooltip())
        self.recording_indicator.refresh_hotkey_tooltips()
        self._update_hotkey_chip()

    def _update_hotkey_chip(self):
        """Muestra en vivo el atajo de grabación actual, siempre visible."""
        hint = get_hotkey_display("toggle_record")
        self.hotkey_chip.setText(f"Grabar: {hint}" if hint else "Grabar")

    def set_collapsed_tooltip(self, collapsed: bool):
        self.edge_button.setToolTip(self._edge_tooltip(collapsed))

    def set_compact_header(self, compact: bool):
        """En modo compacto, oculta chrome secundario: solo logo, título,
        indicador de grabación, expansión y colapsar quedan visibles."""
        self.hotkey_chip.setVisible(not compact)
        self.capture_button.setVisible(not compact)
        self.settings_button.setVisible(not compact)
