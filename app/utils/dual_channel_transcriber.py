import queue
import threading
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import speech_recognition as sr


class DualChannelTranscriber:
    def __init__(
        self,
        language: str = "es-ES",
        mic_device_index: Optional[int] = None,
        system_device_index: Optional[int] = None,
        mic_mode: str = "auto",
        mic_energy_threshold: int = 150,
        mic_dynamic: bool = True,
        mic_adjust_duration: float = 0.8,
        phrase_time_limit: int = 8,
        system_chunk_seconds: int = 6,
        on_text: Optional[Callable[[str, str], None]] = None,
    ):
        self.language = language
        self.mic_device_index = mic_device_index
        self.system_device_index = system_device_index
        self.mic_mode = mic_mode
        self.mic_energy_threshold = mic_energy_threshold
        self.mic_dynamic = mic_dynamic
        self.mic_adjust_duration = mic_adjust_duration
        self.phrase_time_limit = phrase_time_limit
        self.system_chunk_seconds = system_chunk_seconds
        self.on_text = on_text

        self._buffer = []
        self._lock = threading.Lock()

        self._stop_mic = None
        self._stop_sys = None
        self._sys_stream = None
        self._sys_thread = None
        self._sys_queue = queue.Queue()
        self._sys_stop_event = threading.Event()
        self._running = False

    def _append_text(self, origin: str, text: str):
        with self._lock:
            self._buffer.append(f"{origin}: {text}")
        if self.on_text:
            self.on_text(origin, text)

    def get_buffer_text(self, clear: bool = False) -> str:
        with self._lock:
            texto = "\n".join(self._buffer)
            if clear:
                self._buffer.clear()
            return texto

    def start(self):
        if self._running:
            return
        self._running = True
        self._start_mic()
        self._start_system()

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._stop_mic:
            self._stop_mic(wait_for_stop=False)
            self._stop_mic = None

        if self._stop_sys:
            self._stop_sys()
            self._stop_sys = None

    def clear_buffer(self):
        with self._lock:
            self._buffer.clear()

    def set_devices(self, mic_device_index: Optional[int], system_device_index: Optional[int]):
        self.mic_device_index = mic_device_index
        self.system_device_index = system_device_index

    def set_mic_settings(
        self,
        mic_mode: str,
        mic_energy_threshold: int,
        mic_dynamic: bool,
        mic_adjust_duration: float,
    ):
        self.mic_mode = mic_mode
        self.mic_energy_threshold = mic_energy_threshold
        self.mic_dynamic = mic_dynamic
        self.mic_adjust_duration = mic_adjust_duration

    def _start_mic(self):
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = self.mic_dynamic
        recognizer.energy_threshold = self.mic_energy_threshold

        mic = sr.Microphone(device_index=self.mic_device_index)

        if self.mic_mode == "auto":
            try:
                with mic as source:
                    recognizer.adjust_for_ambient_noise(source, duration=self.mic_adjust_duration)
            except Exception:
                pass

        def _callback(rec, audio):
            try:
                texto = rec.recognize_google(audio, language=self.language)
                if texto:
                    self._append_text("YO", texto)
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[YO] Error de red: {e}")

        self._stop_mic = recognizer.listen_in_background(
            mic, _callback, phrase_time_limit=self.phrase_time_limit
        )

    def _wasapi_settings_loopback(self):
        try:
            return sd.WasapiSettings(loopback=True), True
        except TypeError:
            return sd.WasapiSettings(), False

    def supports_system_loopback(self) -> bool:
        return self._wasapi_settings_loopback()[1]

    def _find_wasapi_loopback(self):
        hostapis = sd.query_hostapis()
        candidates = []
        fallback = None
        for i, info in enumerate(sd.query_devices()):
            api = hostapis[info.get("hostapi", 0)].get("name", "")
            name = info.get("name", "")
            if "WASAPI" not in api or info.get("max_input_channels", 0) <= 0:
                continue
            name_lower = name.lower()
            if "loopback" in name_lower:
                return i
            if "mezcla" in name_lower or "stereo mix" in name_lower or "mix" in name_lower:
                candidates.append(i)
            if fallback is None:
                fallback = i
        if candidates:
            return candidates[0]
        return fallback

    def _start_system(self):
        wasapi, supports_loopback = self._wasapi_settings_loopback()

        device_index = self.system_device_index
        if supports_loopback:
            if device_index is None:
                device_index = sd.default.device[1]
            if device_index is None:
                for i, info in enumerate(sd.query_devices()):
                    if info.get("max_output_channels", 0) > 0:
                        device_index = i
                        break
            if device_index is None:
                raise RuntimeError("No se encontro un dispositivo de salida para loopback")
        else:
            if device_index is None:
                device_index = self._find_wasapi_loopback()
            if device_index is None:
                raise RuntimeError("No se encontro un dispositivo de captura WASAPI")

        device_info = sd.query_devices(device_index)
        hostapis = sd.query_hostapis()
        api_name = hostapis[device_info.get("hostapi", 0)].get("name", "?")

        if supports_loopback and "WASAPI" not in api_name:
            if self.system_device_index is not None:
                raise RuntimeError("El dispositivo del sistema debe ser WASAPI para loopback")
            for i, info in enumerate(sd.query_devices()):
                api = hostapis[info.get("hostapi", 0)].get("name", "")
                if "WASAPI" in api and info.get("max_output_channels", 0) > 0:
                    device_index = i
                    device_info = info
                    api_name = api
                    break

        print(f"[SISTEMA] Usando dispositivo {device_index} ({api_name}): {device_info.get('name')}")
        if not supports_loopback and device_info.get("max_input_channels", 0) <= 0:
            raise RuntimeError("El dispositivo del sistema debe ser de entrada (WASAPI) para loopback")

        sample_rate = int(device_info.get("default_samplerate", 44100))

        if supports_loopback:
            max_out = int(device_info.get("max_output_channels", 2))
            channels = 2 if max_out >= 2 else 1
        else:
            max_in = int(device_info.get("max_input_channels", 2))
            channels = 2 if max_in >= 2 else 1

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        bytes_per_sample = 2
        target_bytes = int(sample_rate * self.system_chunk_seconds * bytes_per_sample)

        self._sys_stop_event.clear()

        def _callback(indata, frames, time_info, status):
            if status:
                print(f"[SISTEMA] Loopback status: {status}")
            if self._sys_stop_event.is_set():
                return
            audio = indata
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
            audio = audio.astype(np.int16)
            self._sys_queue.put(audio.tobytes())

        def _worker():
            buffer = bytearray()
            while not self._sys_stop_event.is_set():
                try:
                    data = self._sys_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                buffer.extend(data)
                if len(buffer) >= target_bytes:
                    audio_bytes = bytes(buffer[:target_bytes])
                    buffer = buffer[target_bytes:]
                    audio = sr.AudioData(audio_bytes, sample_rate, bytes_per_sample)
                    try:
                        texto = recognizer.recognize_google(audio, language=self.language)
                        if texto:
                            self._append_text("SISTEMA", texto)
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"[SISTEMA] Error de red: {e}")

        self._sys_stream = sd.InputStream(
            samplerate=sample_rate,
            device=device_index,
            channels=channels,
            dtype="int16",
            callback=_callback,
            extra_settings=wasapi,
        )
        self._sys_stream.start()

        self._sys_thread = threading.Thread(target=_worker, daemon=True)
        self._sys_thread.start()

        def _stop_sys(wait_for_stop: bool = False):
            self._sys_stop_event.set()
            if self._sys_stream:
                self._sys_stream.stop()
                self._sys_stream.close()
                self._sys_stream = None
            if wait_for_stop and self._sys_thread:
                self._sys_thread.join(timeout=2)

        self._stop_sys = _stop_sys
