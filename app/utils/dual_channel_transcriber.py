import queue
import threading
import time
import ctypes
from typing import Callable, Optional

import numpy as np
import soundcard as sc
import sounddevice as sd
import speech_recognition as sr

from app.utils.logger import get_logger

logger = get_logger(__name__)


class DualChannelTranscriber:
    def __init__(
        self,
        language: str = "es-ES",
        stt_provider: str = "google",
        whisper_model: str = "tiny",
        mic_device_index: Optional[int] = None,
        system_device_index: Optional[int] = None,
        capture_mode: str = "both",
        mic_mode: str = "auto",
        mic_energy_threshold: int = 150,
        mic_dynamic: bool = True,
        mic_adjust_duration: float = 0.8,
        phrase_time_limit: int = 8,
        system_chunk_seconds: int = 6,
        on_text: Optional[Callable[[str, str], None]] = None,
        on_audio_level: Optional[Callable[[float], None]] = None,
    ):
        self.language = language
        self.stt_provider = stt_provider
        self.whisper_model_size = whisper_model
        self._whisper_model = None
        self._vad = None
        self.mic_device_index = mic_device_index
        self.system_device_index = system_device_index
        self.capture_mode = capture_mode
        self.mic_mode = mic_mode
        self.mic_energy_threshold = mic_energy_threshold
        self.mic_dynamic = mic_dynamic
        self.mic_adjust_duration = mic_adjust_duration
        self.phrase_time_limit = phrase_time_limit
        self.system_chunk_seconds = system_chunk_seconds
        self.on_text = on_text
        self.on_audio_level = on_audio_level

        self._buffer = []
        self._lock = threading.Lock()

        self._stop_mic = None
        self._stop_sys = None
        self._sys_stream = None
        self._sys_thread = None
        self._sys_queue = queue.Queue()
        self._sys_stop_event = threading.Event()
        self._mic_stream = None
        self._mic_thread = None
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
            return True, []
            
        if self.stt_provider == "whisper" and self._whisper_model is None:
            try:
                import webrtcvad
                from faster_whisper import WhisperModel
                logger.info("[SISTEMA] Cargando modelo Whisper '%s'...", self.whisper_model_size)
                self._vad = webrtcvad.Vad(3)
                self._whisper_model = WhisperModel(self.whisper_model_size, device="cpu", compute_type="int8")
            except Exception as e:
                logger.exception("[SISTEMA] Error cargando Whisper")
                return False, [f"No se pudo cargar el modelo de voz: {e}"]
        warnings = []
        started_any = False
        self._running = True

        if self.capture_mode in ("mic", "both"):
            try:
                self._start_mic()
                started_any = True
            except Exception:
                logger.exception("[YO] No se pudo iniciar micrófono")
                warnings.append("No se pudo iniciar el micrófono")

        if self.capture_mode in ("system", "both"):
            try:
                self._start_system()
                started_any = True
            except Exception:
                logger.exception("[SISTEMA] No se pudo iniciar audio del sistema")
                warnings.append("No se pudo iniciar el audio del sistema")

        if not started_any:
            self._running = False
            warnings.append("No se pudo iniciar ninguna fuente de audio. Comprueba tus dispositivos.")
        return started_any, warnings

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

    def set_capture_mode(self, capture_mode: str):
        if capture_mode not in ("mic", "system", "both"):
            return True, [], self._running
        if capture_mode == self.capture_mode:
            return True, [], self._running

        was_running = self._running
        self.capture_mode = capture_mode
        if was_running:
            self.stop()
            started, warnings = self.start()
            return started, warnings, True
        return True, [], False

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
        device_index = self.mic_device_index
        if device_index is None:
            device_index = sd.default.device[0]

        device_info = sd.query_devices(device_index)
        hostapis = sd.query_hostapis()
        api_name = hostapis[device_info.get("hostapi", 0)].get("name", "?")

        max_in = int(device_info.get("max_input_channels", 1))
        channels = 1 if max_in >= 1 else 0
        if channels == 0:
            raise RuntimeError("El dispositivo de micrófono no tiene canales de entrada")

        sample_rate = int(device_info.get("default_samplerate", 44100))
        bytes_per_sample = 2

        logger.info("[YO] Usando dispositivo %s (%s): %s", device_index, api_name, device_info.get('name'))

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = self.mic_dynamic
        recognizer.energy_threshold = self.mic_energy_threshold

        self._mic_stop_event = threading.Event()
        self._mic_queue = queue.Queue()
        threshold = float(self.mic_energy_threshold)

        if self.stt_provider == "whisper":
            sample_rate = 16000
            bytes_per_sample = 2
            frame_duration_ms = 30
            frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
            
            logger.info("[YO] Usando dispositivo %s (%s): %s a %sHz (Whisper)", device_index, api_name, device_info.get('name'), sample_rate)

            def _callback(indata, frames, time_info, status):
                if self._mic_stop_event.is_set(): return
                audio = indata
                if audio.ndim > 1: audio = np.mean(audio, axis=1)
                audio_int16 = audio.astype(np.int16)
                self._mic_queue.put(audio_int16.tobytes())
                # Emitir nivel de audio para VU meter
                if self.on_audio_level:
                    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
                    level = min(1.0, rms / 5000.0)
                    self.on_audio_level(level)

            def _worker():
                speech_buffer = bytearray()
                is_speaking = False
                silence_frames = 0
                max_silence_frames = int(0.6 / (frame_duration_ms / 1000.0))

                while not self._mic_stop_event.is_set():
                    try:
                        frame = self._mic_queue.get(timeout=0.2)
                    except queue.Empty:
                        continue
                    
                    if len(frame) != frame_size * 2: continue
                        
                    is_speech = self._vad.is_speech(frame, sample_rate)
                    
                    if is_speech:
                        if not is_speaking: is_speaking = True
                        speech_buffer.extend(frame)
                        silence_frames = 0
                    else:
                        if is_speaking:
                            speech_buffer.extend(frame)
                            silence_frames += 1
                            if silence_frames >= max_silence_frames:
                                audio_np = np.frombuffer(bytes(speech_buffer), dtype=np.int16).astype(np.float32) / 32768.0
                                if len(audio_np) > sample_rate * 0.5:
                                    try:
                                        segments, _ = self._whisper_model.transcribe(audio_np, language="es", beam_size=5)
                                        texto = " ".join([s.text for s in segments]).strip()
                                        if texto: self._append_text("YO", texto)
                                    except Exception:
                                        logger.exception("[YO] Error Whisper")
                                speech_buffer = bytearray()
                                is_speaking = False
                                silence_frames = 0

            self._mic_stream = sd.InputStream(
                samplerate=sample_rate, device=device_index, channels=channels,
                dtype="int16", blocksize=frame_size, callback=_callback
            )
            self._mic_stream.start()
            self._mic_thread = threading.Thread(target=_worker, daemon=True)
            self._mic_thread.start()

            def _stop_mic_fn(wait_for_stop=False):
                self._mic_stop_event.set()
                if self._mic_stream:
                    self._mic_stream.stop()
                    self._mic_stream.close()
                    self._mic_stream = None
                if wait_for_stop and self._mic_thread:
                    self._mic_thread.join(timeout=2)
            self._stop_mic = _stop_mic_fn
            return


        def _callback(indata, frames, time_info, status):
            if self._mic_stop_event.is_set():
                return
            audio = indata
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
            audio = audio.astype(np.int16)
            rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
            self._mic_queue.put((audio.tobytes(), rms))
            # Emitir nivel de audio para VU meter
            if self.on_audio_level:
                level = min(1.0, rms / 5000.0)
                self.on_audio_level(level)

        def _worker():
            nonlocal threshold
            speech_buffer = bytearray()
            in_speech = False
            silence_start = 0.0
            phrase_start = 0.0
            ambient_buf = bytearray()
            ambient_ready = False
            ambient_needed = int(sample_rate * self.mic_adjust_duration * bytes_per_sample)

            while not self._mic_stop_event.is_set():
                try:
                    data, rms = self._mic_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if self.mic_mode == "auto" and not ambient_ready:
                    ambient_buf.extend(data)
                    if len(ambient_buf) >= ambient_needed:
                        arr = np.frombuffer(bytes(ambient_buf[:ambient_needed]), dtype=np.int16).astype(np.float64)
                        ambient_rms = np.sqrt(np.mean(arr ** 2))
                        threshold = max(ambient_rms * 2.0, 50.0)
                        recognizer.energy_threshold = threshold
                        logger.info("[YO] Umbral de ruido ajustado: %.1f", threshold)
                        ambient_buf = bytearray()
                        ambient_ready = True
                    continue

                is_speech = rms >= threshold

                if is_speech:
                    if not in_speech:
                        in_speech = True
                        phrase_start = time.time()
                    speech_buffer.extend(data)
                    silence_start = 0.0

                    if self.phrase_time_limit > 0 and len(speech_buffer) > sample_rate * bytes_per_sample:
                        if time.time() - phrase_start >= self.phrase_time_limit:
                            audio = sr.AudioData(bytes(speech_buffer), sample_rate, bytes_per_sample)
                            try:
                                texto = recognizer.recognize_google(audio, language=self.language)
                                if texto:
                                    self._append_text("YO", texto)
                            except sr.UnknownValueError:
                                pass
                            except sr.RequestError:
                                logger.exception("[YO] Error de red")
                            speech_buffer = bytearray()
                            in_speech = False
                            phrase_start = time.time()
                else:
                    if in_speech:
                        if silence_start == 0.0:
                            silence_start = time.time()
                        elif time.time() - silence_start >= 0.5:
                            if len(speech_buffer) >= sample_rate * bytes_per_sample:
                                audio = sr.AudioData(bytes(speech_buffer), sample_rate, bytes_per_sample)
                                try:
                                    texto = recognizer.recognize_google(audio, language=self.language)
                                    if texto:
                                        self._append_text("YO", texto)
                                except sr.UnknownValueError:
                                    pass
                                except sr.RequestError:
                                    logger.exception("[YO] Error de red")
                            speech_buffer = bytearray()
                            in_speech = False
                            silence_start = 0.0
                    elif ambient_ready and self.mic_dynamic:
                        threshold = threshold * 0.99 + rms * 0.01

        self._mic_stream = sd.InputStream(
            samplerate=sample_rate,
            device=device_index,
            channels=channels,
            dtype="int16",
            callback=_callback,
        )
        self._mic_stream.start()

        self._mic_thread = threading.Thread(target=_worker, daemon=True)
        self._mic_thread.start()

        def _stop_mic_fn(wait_for_stop=False):
            self._mic_stop_event.set()
            if self._mic_stream:
                self._mic_stream.stop()
                self._mic_stream.close()
                self._mic_stream = None
            if wait_for_stop and self._mic_thread:
                self._mic_thread.join(timeout=2)

        self._stop_mic = _stop_mic_fn

    def _wasapi_settings_loopback(self):
        for i, info in enumerate(sd.query_devices()):
            api = sd.query_hostapis()[info["hostapi"]]["name"]
            if "WASAPI" in api and "loopback" in info.get("name", "").lower():
                return sd.WasapiSettings(), True
        return sd.WasapiSettings(), False

    def supports_system_loopback(self) -> bool:
        return self._wasapi_settings_loopback()[1]

    def _find_loopback_device(self):
        for i, info in enumerate(sd.query_devices()):
            if info.get("max_input_channels", 0) <= 0:
                continue
            if "loopback" in info.get("name", "").lower():
                return i
        for i, info in enumerate(sd.query_devices()):
            if info.get("max_input_channels", 0) <= 0:
                continue
            name = info.get("name", "").lower()
            if "mezcla" in name or "stereo mix" in name or "mix" in name:
                return i
        return None

    def _start_system(self):
        # Usamos soundcard para loopback real del sistema
        device_id = self.system_device_index
        
        try:
            if device_id is None:
                speaker = sc.default_speaker()
            else:
                # Intentar encontrar por índice o nombre si es posible
                speakers = sc.all_speakers()
                if isinstance(device_id, int) and 0 <= device_id < len(speakers):
                    speaker = speakers[device_id]
                else:
                    speaker = sc.default_speaker()
            
            # Obtener el micrófono de loopback para ese altavoz
            mic = sc.get_microphone(speaker.name, include_loopback=True)
            logger.info("[SISTEMA] Capturando loopback de: %s", speaker.name)
        except Exception as e:
            raise RuntimeError(f"No se pudo inicializar soundcard para loopback: {e}")

        sample_rate = 16000 # Forzamos 16kHz para mejor compatibilidad con Google STT
        
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        bytes_per_sample = 2
        # Chunk de aprox 6 segundos
        chunk_frames = int(sample_rate * self.system_chunk_seconds)

        self._sys_stop_event.clear()

        def _worker():
            # Solucion al error 0x800401f0 (CoInitialize no llamado)
            ctypes.windll.ole32.CoInitialize(None)
            
            sub_frames = int(sample_rate * 0.5)

            if self.stt_provider == "whisper":
                try:
                    with mic.recorder(samplerate=sample_rate) as recorder:
                        accumulated = []
                        total_frames = 0
                        target_frames = sample_rate * 3
                        while not self._sys_stop_event.is_set():
                            try:
                                sub_data = recorder.record(numframes=sub_frames)
                                accumulated.append(sub_data)
                                total_frames += len(sub_data)
                                if total_frames < target_frames:
                                    continue
                                data = np.concatenate(accumulated, axis=0)
                                accumulated = []
                                total_frames = 0
                                if data.ndim > 1:
                                    data = np.mean(data, axis=1)
                                audio_np = data.astype(np.float32)
                                
                                rms = np.sqrt(np.mean(audio_np ** 2))
                                if rms > 0.002: # Only process if there's actual sound
                                    segments, _ = self._whisper_model.transcribe(audio_np, language="es", beam_size=5)
                                    texto = " ".join([s.text for s in segments]).strip()
                                    if texto: self._append_text("SISTEMA", texto)
                            except Exception:
                                if not self._sys_stop_event.is_set():
                                    logger.exception("[SISTEMA] Error en captura")
                                break
                finally:
                    ctypes.windll.ole32.CoUninitialize()
                return


            try:
                with mic.recorder(samplerate=sample_rate) as recorder:
                    accumulated = []
                    total_frames = 0
                    while not self._sys_stop_event.is_set():
                        try:
                            sub_data = recorder.record(numframes=sub_frames)
                            accumulated.append(sub_data)
                            total_frames += len(sub_data)
                            if total_frames < chunk_frames:
                                continue
                            data = np.concatenate(accumulated, axis=0)
                            accumulated = []
                            total_frames = 0
                            
                            # Convertir a mono si es necesario
                            if data.ndim > 1:
                                data = np.mean(data, axis=1)
                            
                            # Convertir a int16 para SpeechRecognition
                            audio_int16 = (data * 32767).astype(np.int16)
                            audio_bytes = audio_int16.tobytes()
                            
                            audio_data = sr.AudioData(audio_bytes, sample_rate, bytes_per_sample)
                            
                            try:
                                texto = recognizer.recognize_google(audio_data, language=self.language)
                                if texto:
                                    self._append_text("SISTEMA", texto)
                            except sr.UnknownValueError:
                                pass
                            except sr.RequestError:
                                logger.exception("[SISTEMA] Error de red")
                                
                        except Exception:
                            if not self._sys_stop_event.is_set():
                                logger.exception("[SISTEMA] Error en captura")
                            break
            finally:
                ctypes.windll.ole32.CoUninitialize()

        self._sys_thread = threading.Thread(target=_worker, daemon=True)
        self._sys_thread.start()

        def _stop_sys(wait_for_stop: bool = False):
            self._sys_stop_event.set()
            if wait_for_stop and self._sys_thread:
                self._sys_thread.join(timeout=2)

        self._stop_sys = _stop_sys
