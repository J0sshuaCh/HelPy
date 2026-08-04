from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor
from app.ui.themes import PALETAS, obtener_qss, normalizar_tema
from app.ui.shared.icons import set_icon_color

class ThemeManager:
    def __init__(self, settings, main_window):
        self.settings = settings
        self.main_window = main_window

    def apply_initial_theme(self, combo_box):
        tema_guardado = normalizar_tema(self.settings.get("tema", "Slate Minimalist (Clásico)"))
        combo_box.setCurrentText(tema_guardado)
        self.cambiar_tema_interfaz(tema_guardado)

    def cambiar_tema_interfaz(self, nombre_tema):
        nombre_tema = normalizar_tema(nombre_tema)
        self.settings.set("tema", nombre_tema)
        theme_data = PALETAS.get(nombre_tema, PALETAS["Slate Minimalist (Clásico)"])
        set_icon_color(theme_data["texto"])
        self.main_window.setStyleSheet(obtener_qss(nombre_tema))
        if hasattr(self.main_window, "reload_icons"):
            self.main_window.reload_icons()
        spinner_color = QColor(theme_data["resaltado"])
        if hasattr(self.main_window, "status_spinner"):
            self.main_window.status_spinner.set_color(spinner_color)
        if hasattr(self.main_window, "overlay"):
            self.main_window.overlay.spinner.set_color(spinner_color)
            self.main_window.overlay.set_theme(
                theme_data.get("scrim", "rgba(0, 0, 0, 140)"),
                QColor(theme_data["texto"]),
            )
        if hasattr(self.main_window, "recording_panel"):
            vu_meter = getattr(self.main_window.recording_panel, "vu_meter", None)
            if vu_meter is not None:
                vu_meter.set_theme(
                    theme_data["vu_track"],
                    theme_data["vu_verde"],
                    theme_data["vu_ambar"],
                    theme_data["vu_rojo"],
                    theme_data["vu_pico"],
                )
        if hasattr(self.main_window, "header_area"):
            indicator = getattr(self.main_window.header_area, "recording_indicator", None)
            if indicator is not None:
                indicator.set_theme(
                    QColor(theme_data["vu_rojo"]),
                    QColor(theme_data["texto_secundario"]),
                )
        if hasattr(self.main_window, "context_panel"):
            p = self.main_window.context_panel
            if hasattr(p, "context_spinner"):
                p.context_spinner.set_color(spinner_color)
        
        # Actualizar otras ventanas
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "cambiar_tema_interfaz") and widget != self.main_window:
                widget.cambiar_tema_interfaz(nombre_tema)
