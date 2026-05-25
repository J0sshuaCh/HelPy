import sys
from PyQt5.QtWidgets import QApplication
from ui.invisible_window import InvisibleWindow


def main():
    print("Iniciando AYUDIN...")

    app = QApplication(sys.argv)
    window = InvisibleWindow()

    print("AYUDIN listo.")
    print("  - Presiona Esc para salir")
    print("  - Usa el icono en la bandeja del sistema para grabar/detener")
    print("  - La ventana captura audio del sistema (Stereo Mix)")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
