import sys
from PyQt5.QtWidgets import QApplication
from app.ui.script_window import ScriptWindow


def _try_create_overlay_window():
    try:
        from app.ui.overlay_window import OverlayWindow

        return OverlayWindow()
    except Exception as exc:
        # Keep ScriptWindow usable even if overlay dependencies are missing.
        print(f"No se pudo iniciar OverlayWindow: {exc}")
        return None


def main():
    print("Iniciando AYUDIN...")

    app = QApplication(sys.argv)
    window = _try_create_overlay_window()
    script = ScriptWindow()

    print("AYUDIN listo.")
    print("  - Presiona Esc para salir")
    print("  - Usa el icono en la bandeja del sistema para grabar/detener")
    print("  - La ventana captura audio del sistema (Stereo Mix)")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
