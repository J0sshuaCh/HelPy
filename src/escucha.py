import queue
import threading
import time

import speech_recognition as sr
import sounddevice as sd
import numpy as np

def escuchar_dispositivo(device_index: int, nombre: str, callback_texto):
    """
    Escucha en bucle (bloqueante). Útil para pruebas simples.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    print(f"[{nombre}] Iniciando canal en dispositivo {device_index}...")

    while True:
        try:
            with sr.Microphone(device_index=device_index) as source:
                print(f"[{nombre}] Escuchando...")
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=8)

                try:
                    print(f"[{nombre}] Transcribiendo...")
                    texto = recognizer.recognize_google(audio, language="es-ES")
                    if texto:
                        callback_texto(nombre, texto)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"[{nombre}] Error de red: {e}")
                    time.sleep(2)
        except Exception as e:
            print(f"[{nombre}] Error de hardware (¿Dispositivo ocupado?): {e}")
            time.sleep(2)


def iniciar_escucha_en_segundo_plano(device_index: int, nombre: str, callback_texto):
    """
    Inicia escucha no bloqueante usando listen_in_background.
    Retorna una función para detener la captura.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    mic = sr.Microphone(device_index=device_index)

    def _callback(rec, audio):
        try:
            texto = rec.recognize_google(audio, language="es-ES")
            if texto:
                callback_texto(nombre, texto)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"[{nombre}] Error de red: {e}")

    print(f"[{nombre}] Iniciando escucha en segundo plano (dispositivo {device_index})...")
    stop_fn = recognizer.listen_in_background(mic, _callback, phrase_time_limit=8)
    return stop_fn


def listar_dispositivos_sounddevice():
    dispositivos = sd.query_devices()
    hostapis = sd.query_hostapis()
    for i, info in enumerate(dispositivos):
        tipo = "IN" if info.get("max_input_channels", 0) > 0 else "OUT"
        nombre = info.get("name", "Desconocido")
        api = hostapis[info.get("hostapi", 0)].get("name", "?")
        print(f"SD {i} [{tipo}] ({api}): {nombre}")


def _wasapi_settings_loopback():
    try:
        return sd.WasapiSettings(loopback=True), True
    except TypeError:
        return sd.WasapiSettings(), False


def _buscar_loopback_wasapi():
    hostapis = sd.query_hostapis()
    candidatos = []
    fallback = None
    for i, info in enumerate(sd.query_devices()):
        api = hostapis[info.get("hostapi", 0)].get("name", "")
        nombre = info.get("name", "")
        if "WASAPI" not in api or info.get("max_input_channels", 0) <= 0:
            continue
        nombre_min = nombre.lower()
        if "loopback" in nombre_min:
            return i
        if "mezcla" in nombre_min or "stereo mix" in nombre_min or "mix" in nombre_min:
            candidatos.append(i)
        if fallback is None:
            fallback = i
    if candidatos:
        return candidatos[0]
    return fallback


def iniciar_escucha_sistema_loopback(nombre: str, callback_texto, device_index: int = None,
                                     sample_rate: int = None, chunk_seconds: int = 6):
    """
    Captura el audio del sistema usando WASAPI loopback (Windows) con sounddevice.
    Retorna una funcion para detener la captura.
    """
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    wasapi, soporta_loopback = _wasapi_settings_loopback()

    dispositivo_index = device_index
    if soporta_loopback:
        if dispositivo_index is None:
            dispositivo_index = sd.default.device[1]
        if dispositivo_index is None:
            for i, info in enumerate(sd.query_devices()):
                if info.get("max_output_channels", 0) > 0:
                    dispositivo_index = i
                    break
        if dispositivo_index is None:
            raise RuntimeError("No se encontro un dispositivo de salida para loopback")
    else:
        if dispositivo_index is None:
            dispositivo_index = _buscar_loopback_wasapi()
        if dispositivo_index is None:
            raise RuntimeError("No se encontro un dispositivo de captura WASAPI")

    dispositivo_info = sd.query_devices(dispositivo_index)
    if sample_rate is None:
        sample_rate = int(dispositivo_info.get("default_samplerate", 44100))

    if soporta_loopback:
        max_out = int(dispositivo_info.get("max_output_channels", 2))
        canales = 2 if max_out >= 2 else 1
    else:
        max_in = int(dispositivo_info.get("max_input_channels", 2))
        canales = 2 if max_in >= 2 else 1
    detener_evento = threading.Event()
    cola = queue.Queue()

    bytes_por_muestra = 2
    bytes_objetivo = sample_rate * chunk_seconds * bytes_por_muestra

    def _callback(indata, frames, time_info, status):
        if status:
            print(f"[{nombre}] Loopback status: {status}")
        if detener_evento.is_set():
            return
        audio = indata
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        audio = audio.astype(np.int16)
        cola.put(audio.tobytes())

    def _worker():
        buffer = bytearray()
        while not detener_evento.is_set():
            try:
                data = cola.get(timeout=0.2)
            except queue.Empty:
                continue
            buffer.extend(data)
            if len(buffer) >= bytes_objetivo:
                audio_bytes = bytes(buffer[:bytes_objetivo])
                buffer = buffer[bytes_objetivo:]
                audio = sr.AudioData(audio_bytes, sample_rate, bytes_por_muestra)
                try:
                    texto = recognizer.recognize_google(audio, language="es-ES")
                    if texto:
                        callback_texto(nombre, texto)
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"[{nombre}] Error de red: {e}")

    tipo_disp = "salida" if soporta_loopback else "loopback"
    print(f"[{nombre}] Iniciando loopback (dispositivo {tipo_disp} {dispositivo_index})...")
    stream = sd.InputStream(
        samplerate=sample_rate,
        device=dispositivo_index,
        channels=canales,
        dtype="int16",
        callback=_callback,
        extra_settings=wasapi,
    )
    stream.start()

    hilo = threading.Thread(target=_worker, daemon=True)
    hilo.start()

    def _stop(wait_for_stop: bool = False):
        detener_evento.set()
        stream.stop()
        stream.close()
        if wait_for_stop:
            hilo.join(timeout=2)

    return _stop

def escuchar_usuario(device_index: int = None) -> str:
    """Función síncrona simple para compatibilidad."""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone(device_index=device_index) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            return recognizer.recognize_google(audio, language="es-ES")
    except Exception:
        return ""

def listar_dispositivos():
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"ID {i}: {name}")

if __name__ == "__main__":
    print("Dispositivos detectados:")
    listar_dispositivos()
