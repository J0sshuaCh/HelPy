from typing import Optional, Callable

from app.utils.dual_channel_transcriber import DualChannelTranscriber
from app.core.llm_client import get_llm_client


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
        )
        self._on_result_callback: Optional[Callable[[str], None]] = None
        self._on_status_callback: Optional[Callable[[str], None]] = None
        self._on_llm_callback: Optional[Callable[[str], None]] = None
        self._on_llm_chunk_callback: Optional[Callable[[str], None]] = None
        try:
            self.llm = get_llm_client()
        except Exception as exc:
            self.llm = None
            self._emit_status(f"LLM desactivado: {exc}")

    def on_result(self, callback: Callable[[str], None]):
        self._on_result_callback = callback

    def on_status(self, callback: Callable[[str], None]):
        self._on_status_callback = callback

    def on_llm_result(self, callback: Callable[[str], None]):
        self._on_llm_callback = callback

    def on_llm_chunk(self, callback: Callable[[str], None]):
        self._on_llm_chunk_callback = callback

    def _emit_status(self, msg: str):
        if self._on_status_callback:
            self._on_status_callback(msg)
        print(msg)

    def start_recording(self):
        started, warnings = self.transcriber.start()
        if started:
            self._emit_status("Escuchando...")
        else:
            self._emit_status("No se pudo iniciar la grabacion")
        for warning in warnings:
            self._emit_status(warning)

    def stop_recording_and_transcribe(self):
        self._emit_status("Procesando audio...")
        self.transcriber.stop()

        text = self.transcriber.get_buffer_text(clear=True)
        if text:
            self._emit_status("Transcripción completada")
            if self._on_result_callback:
                self._on_result_callback(text)
        else:
            self._emit_status("No se pudo transcribir el audio")

    def send_buffer_to_llm(self):
        if not self.llm:
            self._emit_status("LLM no disponible")
            return

        self._emit_status("Enviando a IA... Procesando")
        text = self.transcriber.get_buffer_text(clear=False)
        if not text:
            self._emit_status("Buffer vacio")
            return

        if self._on_llm_chunk_callback:
            self._on_llm_chunk_callback("")  # signal to clear text

        def _process_llm():
            try:
                if hasattr(self.llm, 'ask_stream'):
                    full_response = []
                    for chunk in self.llm.ask_stream(text):
                        if chunk:
                            full_response.append(chunk)
                            if self._on_llm_chunk_callback:
                                self._on_llm_chunk_callback(chunk)
                    respuesta = ''.join(full_response)
                else:
                    respuesta = self.llm.ask(text)
                    if respuesta and self._on_llm_chunk_callback:
                        self._on_llm_chunk_callback(respuesta)

                if self._on_llm_callback:
                    self._on_llm_callback(respuesta)
                self._emit_status("IA respondio correctamente")
            except Exception as e:
                error_msg = f"Error LLM: {e}"
                if self._on_llm_chunk_callback:
                    self._on_llm_chunk_callback(error_msg)
                if self._on_llm_callback:
                    self._on_llm_callback(error_msg)
                self._emit_status("Error de IA")

        import threading
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
            return
            
        was_running = self.transcriber._running
        if was_running:
            self.transcriber.stop()
            
        self.transcriber.stt_provider = provider
        if self.transcriber.whisper_model_size != model_size:
            self.transcriber._whisper_model = None
        self.transcriber.whisper_model_size = model_size
        
        if was_running:
            self.start_recording()

    def set_capture_mode(self, capture_mode: str):
        started, warnings, was_running = self.transcriber.set_capture_mode(capture_mode)
        if was_running:
            if started:
                self._emit_status("Modo actualizado")
            else:
                self._emit_status("No se pudo iniciar la fuente seleccionada")
        for warning in warnings:
            self._emit_status(warning)

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
