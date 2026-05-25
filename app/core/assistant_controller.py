import threading
from typing import Optional, Callable
from app.utils.system_audio_recorder import SystemAudioRecorder
from app.utils.speech_transcriber import SpeechTranscriber


class AssistantController:
    def __init__(self, stt_language: str = "es", stt_backend: str = "whisper"):
        self.recorder = SystemAudioRecorder()
        self.stt = SpeechTranscriber(language=stt_language, backend=stt_backend)
        self._on_result_callback: Optional[Callable[[str], None]] = None
        self._on_status_callback: Optional[Callable[[str], None]] = None

    def on_result(self, callback: Callable[[str], None]):
        self._on_result_callback = callback

    def on_status(self, callback: Callable[[str], None]):
        self._on_status_callback = callback

    def _emit_status(self, msg: str):
        if self._on_status_callback:
            self._on_status_callback(msg)
        print(msg)

    def start_recording(self):
        self._emit_status("Escuchando...")
        self.recorder.start_recording()

    def stop_recording_and_transcribe(self):
        self._emit_status("Procesando audio...")

        def process():
            try:
                self.recorder.stop_recording()
                audio_data = self.recorder.get_audio_data_resampled(16000)

                if audio_data is None:
                    text = None
                else:
                    if isinstance(audio_data, bytes) and len(audio_data) > 44:
                        text = self.stt.transcribe(audio_data)
                    else:
                        text = None

                if text:
                    self._emit_status("Transcripción completada")
                    if self._on_result_callback:
                        self._on_result_callback(text)
                else:
                    self._emit_status("No se pudo transcribir el audio")

            except Exception as e:
                self._emit_status(f"Error: {e}")

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def transcribe_file(self, filepath: str) -> Optional[str]:
        self._emit_status("Transcribiendo archivo...")
        text = self.stt.transcribe_file(filepath)
        if text:
            self._emit_status("Transcripción completada")
        else:
            self._emit_status("No se pudo transcribir")
        return text

    def cleanup(self):
        self.recorder.cleanup()
        self.stt.cleanup()
