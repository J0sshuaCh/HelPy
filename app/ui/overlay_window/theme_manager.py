from PyQt5.QtWidgets import QApplication
from app.ui.themes import obtener_qss

class ThemeManager:
    def __init__(self, settings, main_window):
        self.settings = settings
        self.main_window = main_window

    def apply_initial_theme(self, combo_box):
        tema_guardado = self.settings.get("tema", "Slate Minimalist")
        combo_box.setCurrentText(tema_guardado)
        self.cambiar_tema_interfaz(tema_guardado)

    def cambiar_tema_interfaz(self, nombre_tema):
        self.settings.set("tema", nombre_tema)
        self.main_window.setStyleSheet(obtener_qss(nombre_tema))
        
        # Actualizar otras ventanas
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "cambiar_tema_interfaz") and widget != self.main_window:
                widget.cambiar_tema_interfaz(nombre_tema)
