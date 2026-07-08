import sys
import os
import ctypes

# Asignar identidad propia en Windows para mostrar icono correcto en taskbar
myappid = 'helpy.app.v1'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# Solucionar conflicto de DLL en Windows entre torch (faster-whisper) y PyQt5
try:
    import torch
    import faster_whisper
except ImportError:
    pass

# Hook seguro para DLLs de llama.cpp
if getattr(sys, 'frozen', False):
    try:
        # Intentamos añadir la carpeta de DLLs si existe
        dll_path = os.path.join(sys._MEIPASS, 'llama_cpp', 'lib')
        if os.path.exists(dll_path):
            os.add_dll_directory(dll_path)
    except Exception:
        pass # Ignoramos errores de carga de DLL, si falla, Windows intentará buscar por defecto

import tempfile
import traceback
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from app.ui.script_window import ScriptWindow

def _try_create_overlay_window():
    try:
        from app.ui.overlay_window import OverlayWindow
        return OverlayWindow()
    except Exception as e:
        print("\n" + "="*50)
        print(f"ERROR AL INICIAR OverlayWindow: {e}")
        traceback.print_exc()
        print("="*50 + "\n")
        
        log_dir = tempfile.gettempdir()
        log_path = os.path.join(log_dir, "ayudin_overlay_error.log")
        with open(log_path, "w") as f:
            f.write("Error: No se pudo iniciar OverlayWindow. Traceback:\n")
            traceback.print_exc(file=f)
        return None

def main():
    print("Iniciando AYUDIN...")

    app = QApplication(sys.argv)
    
    # Store windows in a list to prevent garbage collection
    windows = []

    app._windows = windows

    # Create script window first
    script_window = ScriptWindow()
    windows.append(script_window)

    # Create overlay window last to ensure it's on top
    overlay_window = _try_create_overlay_window()
    if overlay_window:
        windows.append(overlay_window)

    def _raise_overlay():
        if overlay_window:
            overlay_window.show()
            overlay_window.raise_()
            overlay_window.activateWindow()
            overlay_window.setFocus()

    # Although windows show themselves, this makes it explicit.
    for window in windows:
        if hasattr(window, "show"):
            window.show()

    if overlay_window:
        QTimer.singleShot(200, _raise_overlay)

    print("AYUDIN listo.")
    print("  - Presiona Esc para salir")
    print("  - Usa el icono en la bandeja del sistema para grabar/detener")

    if not overlay_window:
        print("\nAdvertencia: La ventana principal (OverlayWindow) no pudo iniciarse.")
        print("La ventana de script está disponible, pero la funcionalidad principal de transcripción no funcionará.")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
