import threading
import time
from src.escucha import escuchar_dispositivo
from src.cerebro import pensar_respuesta

class TranscriptorDual:
    def __init__(self, mic_index=1, system_index=2):
        self.mic_index = mic_index
        self.system_index = system_index
        self.buffer_conversacion = []
        self.activo = False

    def procesar_texto(self, origen, texto):
        # Etiquetamos quién dijo qué
        entrada = f"{origen}: {texto}"
        print(f"\n[CAPTURA] {entrada}")
        self.buffer_conversacion.append(entrada)
        
        # Si queremos que la IA responda automáticamente al detectar silencio en la llamada:
        # Aquí podrías disparar el 'pensar_respuesta'
        # Por ahora lo guardamos en un historial para la UI

    def iniciar(self):
        self.activo = True
        
        # Hilo para mi voz (Micrófono)
        self.hilo_mic = threading.Thread(
            target=escuchar_dispositivo, 
            args=(self.mic_index, "YO", self.procesar_texto),
            daemon=True
        )
        
        # Hilo para el audio del sistema (Llamada/Otro)
        self.hilo_sys = threading.Thread(
            target=escuchar_dispositivo, 
            args=(self.system_index, "SISTEMA", self.procesar_texto),
            daemon=True
        )
        
        print(f"Iniciando captura dual (Mic: {self.mic_index}, Sys: {self.system_index})...")
        self.hilo_mic.start()
        self.hilo_sys.start()

    def detener(self):
        self.activo = False
        print("Captura detenida.")

if __name__ == "__main__":
    # Ajusta los índices según tu 'Mezcla estéreo' y tu Micro real
    # Micro (TE-9072) -> 1
    # Mezcla estéreo -> 2
    transcriptor = TranscriptorDual(mic_index=1, system_index=2)
    transcriptor.iniciar()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        transcriptor.detener()
