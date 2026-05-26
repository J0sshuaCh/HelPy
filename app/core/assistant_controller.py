from typing import Optional, Callable

from app.utils.dual_channel_transcriber import DualChannelTranscriber
from app.core.llm_client import LlmClient


class AssistantController:
    def __init__(
        self,
        stt_language: str = "es-ES",
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
        self.llm = LlmClient()

    def on_result(self, callback: Callable[[str], None]):
        self._on_result_callback = callback

    def on_status(self, callback: Callable[[str], None]):
        self._on_status_callback = callback

    def on_llm_result(self, callback: Callable[[str], None]):
        self._on_llm_callback = callback

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
        self._emit_status("Enviando a IA... Procesando")
        text = self.transcriber.get_buffer_text(clear=False)
        if not text:
            self._emit_status("Buffer vacio")
            return
            
        def _process_llm():
            try:
                respuesta = self.llm.ask(text)
                if self._on_llm_callback:
                    self._on_llm_callback(respuesta)
                self._emit_status("IA respondio correctamente")
            except Exception as e:
                if self._on_llm_callback:
                    self._on_llm_callback(f"Error LLM: {e}")
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
