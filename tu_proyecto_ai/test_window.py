import sys
from PyQt5.QtWidgets import QApplication
from ui.invisible_window import InvisibleWindow


def main():
    print("Iniciando prueba de ventana invisible...")
    
    app = QApplication(sys.argv)
    window = InvisibleWindow()
    
    # Test: actualizar texto desde otro hilo (simulando respuesta del LLM)
    import threading
    
    def update_text_later():
        import time
        time.sleep(1.5)  # Simular tiempo de respuesta del LLM
        print("Enviando respuesta simulada...")
        window.set_text("Hola! Esta es una respuesta simulada de tu IA asistente.")
    
    thread = threading.Thread(target=update_text_later, daemon=True)
    thread.start()
    
    print("Ventana invisible visible. Presiona Esc o usa el icono en la bandeja del sistema para salir.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
