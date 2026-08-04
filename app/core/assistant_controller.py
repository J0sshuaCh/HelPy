import threading
from typing import Optional, Callable

from app.utils.dual_channel_transcriber import DualChannelTranscriber
from app.core.llm_client import get_llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AssistantController:
    def __init__(
        self,
        stt_language: str = "es-ES",
        stt_provider: str = "google",
        whisper_model: str = "tiny",
        capture_mode: str = "both",
        mic_mode: str = "auto",
        mic_energy_threshold: int = 150,
        mic_dynamic: bool = True,
        mic_adjust_duration: float = 0.8,
        mic_device_index: Optional[int] = None,
        system_device_index: Optional[int] = None,
    ):
        self.transcriber = DualChannelTranscriber(
            language=stt_language,
            stt_provider=stt_provider,
            whisper_model=whisper_model,
            mic_device_index=mic_device_index,
            system_device_index=system_device_index,
            capture_mode=capture_mode,
            mic_mode=mic_mode,
            mic_energy_threshold=mic_energy_threshold,
            mic_dynamic=mic_dynamic,
            mic_adjust_duration=mic_adjust_duration,
            on_text=self._handle_text,
            on_audio_level=self._handle_audio_level,
        )
        self._on_result_callback: Optional[Callable[[str], None]] = None
        self._on_status_callback: Optional[Callable[[str], None]] = None
        self._on_llm_callback: Optional[Callable[[str], None]] = None
        self._on_llm_chunk_callback: Optional[Callable[[str], None]] = None
        self._on_llm_error_callback: Optional[Callable[[str], None]] = None
        self._on_audio_level_callback: Optional[Callable[[float], None]] = None
        self._on_llm_busy_callback: Optional[Callable[[bool], None]] = None
        self._llm_cancel_event = threading.Event()
        self._llm_busy = False
        try:
            self.llm = get_llm_client()
        except Exception:
            logger.exception("Error al iniciar la IA")
            self.llm = None
            self._emit_status("No se pudo iniciar la IA. Revisa la configuración del proveedor.")

    def on_result(self, callback: Callable[[str], None]):
        self._on_result_callback = callback

    def on_status(self, callback: Callable[[str], None]):
        self._on_status_callback = callback

    def on_llm_result(self, callback: Callable[[str], None]):
        self._on_llm_callback = callback

    def on_llm_chunk(self, callback: Callable[[str], None]):
        self._on_llm_chunk_callback = callback

    def on_llm_error(self, callback: Callable[[str], None]):
        self._on_llm_error_callback = callback

    def on_audio_level(self, callback: Callable[[float], None]):
        self._on_audio_level_callback = callback

    def on_llm_busy(self, callback: Callable[[bool], None]):
        self._on_llm_busy_callback = callback

    def is_llm_busy(self) -> bool:
        return self._llm_busy

    def cancel_llm(self):
        self._llm_cancel_event.set()
        self._emit_status("Envío cancelado")

    def _handle_audio_level(self, level: float):
        if self._on_audio_level_callback:
            self._on_audio_level_callback(level)

    def _emit_status(self, msg: str):
        if self._on_status_callback:
            self._on_status_callback(msg)
        logger.info("Estado: %s", msg)

    def start_recording(self):
        started, warnings = self.transcriber.start()
        if started:
            self._emit_status("Escuchando...")
        else:
            self._emit_status("No se pudo iniciar la grabación. Comprueba los dispositivos de audio.")
        for warning in warnings:
            self._emit_status(warning)
        return started, warnings

    def stop_recording_and_transcribe(self):
        self._emit_status("Procesando audio...")
        self.transcriber.stop()

        text = self.transcriber.get_buffer_text(clear=True)
        if text:
            self._emit_status("Transcripción completada")
            if self._on_result_callback:
                self._on_result_callback(text)
        else:
            self._emit_status("No se pudo transcribir el audio. Inténtalo de nuevo.")

    def send_buffer_to_llm(self):
        if self._llm_busy:
            self._emit_status("Envío en curso. Espera a que termine.")
            return
        if not self.llm:
            self._emit_status("No se pudo usar la IA. Revisa la configuración.")
            return

        text = self.transcriber.get_buffer_text(clear=False)
        if not text:
            self._emit_status("No hay texto que enviar. Graba o transcribe algo primero.")
            return

        self._emit_status("Enviando a la IA...")
        self._llm_busy = True
        self._llm_cancel_event.clear()
        if self._on_llm_busy_callback:
            self._on_llm_busy_callback(True)

        if self._on_llm_chunk_callback:
            self._on_llm_chunk_callback("")  # signal to clear text

        def _process_llm():
            try:
                if hasattr(self.llm, 'ask_stream'):
                    full_response = []
                    for chunk in self.llm.ask_stream(text):
                        if self._llm_cancel_event.is_set():
                            break
                        if chunk:
                            full_response.append(chunk)
                            if self._on_llm_chunk_callback:
                                self._on_llm_chunk_callback(chunk)
                    respuesta = ''.join(full_response)
                else:
                    respuesta = self.llm.ask(text)
                    if respuesta and self._on_llm_chunk_callback:
                        self._on_llm_chunk_callback(respuesta)

                if self._llm_cancel_event.is_set():
                    if self._on_llm_callback:
                        self._on_llm_callback("")
                    return
                if self._on_llm_callback:
                    self._on_llm_callback(respuesta)
                self._emit_status("Respuesta de la IA lista")
            except Exception:
                logger.exception("Error al consultar la IA")
                error_msg = (
                    "No se pudo obtener la respuesta de la IA. "
                    "Revisa la conexión y la configuración del proveedor."
                )
                self._emit_status("Sin respuesta de la IA")
                if self._on_llm_error_callback:
                    self._on_llm_error_callback(error_msg)
            finally:
                self._llm_busy = False
                if self._on_llm_busy_callback:
                    self._on_llm_busy_callback(False)

        threading.Thread(target=_process_llm, daemon=True).start()

    def cleanup(self):
        self.transcriber.stop()

    def _handle_text(self, origin: str, text: str):
        if self._on_result_callback:
            self._on_result_callback(f"{origin}: {text}")

    def set_devices(self, mic_device_index: Optional[int], system_device_index: Optional[int]):
        self.transcriber.set_devices(mic_device_index, system_device_index)

    def set_stt_settings(self, provider: str, model_size: str):
        if self.transcriber.stt_provider == provider and self.transcriber.whisper_model_size == model_size:
            return True, self.transcriber._running
            
        was_running = self.transcriber._running
        if was_running:
            self.transcriber.stop()
            
        self.transcriber.stt_provider = provider
        if self.transcriber.whisper_model_size != model_size:
            self.transcriber._whisper_model = None
        self.transcriber.whisper_model_size = model_size
        
        if was_running:
            started, warnings = self.start_recording()
            return started, was_running
        return True, False

    def set_capture_mode(self, capture_mode: str):
        started, warnings, was_running = self.transcriber.set_capture_mode(capture_mode)
        if was_running:
            if started:
                self._emit_status("Modo de captura actualizado")
            else:
                self._emit_status("No se pudo iniciar la captura seleccionada. Revisa los dispositivos.")
        for warning in warnings:
            self._emit_status(warning)
        return started, was_running

    def set_mic_settings(
        self,
        mic_mode: str,
        mic_energy_threshold: int,
        mic_dynamic: bool,
        mic_adjust_duration: float,
    ):
        self.transcriber.set_mic_settings(
            mic_mode=mic_mode,
            mic_energy_threshold=mic_energy_threshold,
            mic_dynamic=mic_dynamic,
            mic_adjust_duration=mic_adjust_duration,
        )

    def supports_system_loopback(self) -> bool:
        return self.transcriber.supports_system_loopback()
