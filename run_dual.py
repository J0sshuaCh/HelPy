import os
import sys
# Agregamos el directorio raíz al path para que reconozca el paquete 'src'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.escucha import iniciar_escucha_en_segundo_plano, iniciar_escucha_sistema_loopback
from src.cerebro import pensar_respuesta
from pynput import keyboard
import time

class TranscriptorDual:
    def __init__(self, mic_index=1, system_index=2):
        self.mic_index = mic_index
        self.system_index = system_index
        self.buffer_conversacion = []
        self.stop_mic = None
        self.stop_sys = None
        self.en_captura = False
        self.atencion_ia = False

    def procesar_texto(self, origen, texto):
        if not self.en_captura:
            return
        entrada = f"{origen}: {texto}"
        print(f"\n[CAPTURA] {entrada}")
        self.buffer_conversacion.append(entrada)

    def _texto_buffer(self):
        if not self.buffer_conversacion:
            return ""
        return "\n".join(self.buffer_conversacion)

    def iniciar(self):
        print(f"Iniciando captura dual (Mic: {self.mic_index}, Sys: {self.system_index})...")
        self.stop_mic = iniciar_escucha_en_segundo_plano(self.mic_index, "YO", self.procesar_texto)
        if self.system_index is None:
            self.stop_sys = iniciar_escucha_sistema_loopback("SISTEMA", self.procesar_texto)
        else:
            self.stop_sys = iniciar_escucha_sistema_loopback("SISTEMA", self.procesar_texto, device_index=self.system_index)
        self.en_captura = True

    def detener(self):
        if self.stop_mic:
            self.stop_mic(wait_for_stop=False)
        if self.stop_sys:
            self.stop_sys(wait_for_stop=False)
        self.en_captura = False
        print("Captura detenida.")

    def toggle_ia(self):
        if self.atencion_ia:
            return
        self.atencion_ia = True
        self.en_captura = False

        texto = self._texto_buffer()
        if not texto:
            print("[IA] Buffer vacio, no se envia.")
            self.atencion_ia = False
            self.en_captura = True
            return

        print("\n[IA] Enviando transcripciones a la IA...")
        respuesta = pensar_respuesta(texto)
        print(f"\n[IA] Respuesta: {respuesta}\n")

        self.buffer_conversacion.clear()
        self.atencion_ia = False
        self.en_captura = True

if __name__ == "__main__":
    print("--- DISPOSITIVOS DISPONIBLES ---")
    from src.escucha import listar_dispositivos, listar_dispositivos_sounddevice
    print("SpeechRecognition (entrada):")
    listar_dispositivos()
    print("\nSoundDevice (salida/loopback):")
    listar_dispositivos_sounddevice()
    print("--------------------------------\n")

    # Mic: indice de entrada (SpeechRecognition)
    # Sys: indice de salida (SoundDevice) o None para usar el default
    transcriptor = TranscriptorDual(mic_index=1, system_index=None)
    transcriptor.iniciar()

    print("Atajo IA: Alt derecho + \\")

    def on_activate():
        transcriptor.toggle_ia()

    with keyboard.GlobalHotKeys({"<alt_gr>+\\": on_activate}) as h:
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            transcriptor.detener()
