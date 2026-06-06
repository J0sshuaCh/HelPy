import sys
import traceback
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from app.ui.script_window import ScriptWindow

def _try_create_overlay_window():
    try:
        from app.ui.overlay_window import OverlayWindow
        return OverlayWindow()
    except Exception as e:
        # Imprimir el error directamente en consola para diagnóstico inmediato
        import traceback
        print("\n" + "="*50)
        print(f"ERROR AL INICIAR OverlayWindow: {e}")
        traceback.print_exc()
        print("="*50 + "\n")
        
        # Mantener el log en archivo por si acaso
        import os
        log_path = os.path.join(os.path.dirname(__file__), "overlay_error.log")
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
