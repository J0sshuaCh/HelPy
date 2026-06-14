from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor
from app.ui.themes import PALETAS, obtener_qss
from app.ui.shared.icons import set_icon_color

class ThemeManager:
    def __init__(self, settings, main_window):
        self.settings = settings
        self.main_window = main_window

    def apply_initial_theme(self, combo_box):
        tema_guardado = self.settings.get("tema", "Slate Minimalist (Clasico)")
        combo_box.setCurrentText(tema_guardado)
        self.cambiar_tema_interfaz(tema_guardado)

    def cambiar_tema_interfaz(self, nombre_tema):
        self.settings.set("tema", nombre_tema)
        theme_data = PALETAS.get(nombre_tema, PALETAS["Slate Minimalist (Clasico)"])
        set_icon_color(theme_data["texto"])
        self.main_window.setStyleSheet(obtener_qss(nombre_tema))
        if hasattr(self.main_window, "reload_icons"):
            self.main_window.reload_icons()
        spinner_color = QColor(theme_data["resaltado"])
        if hasattr(self.main_window, "status_spinner"):
            self.main_window.status_spinner.set_color(spinner_color)
        if hasattr(self.main_window, "overlay"):
            self.main_window.overlay.spinner.set_color(spinner_color)
        if hasattr(self.main_window, "ai_config_panel"):
            p = self.main_window.ai_config_panel
            if hasattr(p, "save_spinner"):
                p.save_spinner.set_color(spinner_color)
            if hasattr(p, "download_spinner"):
                p.download_spinner.set_color(spinner_color)
        if hasattr(self.main_window, "context_panel"):
            p = self.main_window.context_panel
            if hasattr(p, "context_spinner"):
                p.context_spinner.set_color(spinner_color)
        
        # Actualizar otras ventanas
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "cambiar_tema_interfaz") and widget != self.main_window:
                widget.cambiar_tema_interfaz(nombre_tema)
