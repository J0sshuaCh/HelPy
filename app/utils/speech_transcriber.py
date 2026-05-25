import os
import tempfile
from typing import Optional


class SpeechTranscriber:
    def __init__(self, language: str = "es", backend: str = "whisper"):
        self.language = language
        self.backend = backend
        self._whisper_model = None
        self._recognizer = None

    def transcribe(self, audio_data: bytes) -> Optional[str]:
        if self.backend == "whisper":
            return self._transcribe_whisper(audio_data)
        elif self.backend == "google":
            return self._transcribe_google(audio_data)
        elif self.backend == "auto":
            result = self._transcribe_whisper(audio_data)
            if result is None:
                result = self._transcribe_google(audio_data)
            return result
        return None

    def transcribe_file(self, filepath: str) -> Optional[str]:
        with open(filepath, "rb") as f:
            return self.transcribe(f.read())

    def _transcribe_whisper(self, audio_data: bytes) -> Optional[str]:
        try:
            import os
            import sys
            import ctypes
            
            # Explicitly add torch lib directory to DLL search path
            if sys.platform == "win32":
                torch_lib_path = None
                for p in sys.path:
                    # Look for torch/lib in site-packages
                    potential_path = os.path.abspath(os.path.join(p, "torch", "lib"))
                    if os.path.exists(potential_path):
                        torch_lib_path = potential_path
                        break
                
                if torch_lib_path:
                    # Use add_dll_directory first (Python 3.8+)
                    if hasattr(os, "add_dll_directory"):
                        try:
                            os.add_dll_directory(torch_lib_path)
                        except Exception as e:
                            print(f"Warning: add_dll_directory failed: {e}")
                    
                    # Also update PATH and LoadLibrary as fallback/supplement
                    os.environ["PATH"] = torch_lib_path + os.pathsep + os.environ["PATH"]
                    
                    # Manually load core DLLs to 'prime' the process
                    try:
                        ctypes.WinDLL(os.path.join(torch_lib_path, 'c10.dll'))
                        ctypes.WinDLL(os.path.join(torch_lib_path, 'torch_cpu.dll'))
                    except Exception as e:
                        print(f"Warning: manual DLL priming failed: {e}")

            import whisper
            import numpy as np
            import soundfile as sf

            if self._whisper_model is None:
                print("Cargando modelo Whisper...")
                self._whisper_model = whisper.load_model("tiny", device="cpu")
                print("Modelo Whisper listo.")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                with open(tmp_path, "wb") as f:
                    f.write(audio_data)

                result = self._whisper_model.transcribe(
                    tmp_path,
                    language=self.language,
                    fp16=False
                )
                text = result.get("text", "").strip()
                return text if text else None
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        except Exception as e:
            print(f"Error en Whisper: {e}")
            return None

    def _transcribe_google(self, audio_data: bytes) -> Optional[str]:
        try:
            import speech_recognition as sr

            if self._recognizer is None:
                self._recognizer = sr.Recognizer()

            lang_map = {"es": "es-ES", "en": "en-US"}
            lang = lang_map.get(self.language, "es-ES")

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                with open(tmp_path, "wb") as f:
                    f.write(audio_data)

                with sr.AudioFile(tmp_path) as source:
                    audio = self._recognizer.record(source)

                text = self._recognizer.recognize_google(audio, language=lang)
                return text.strip()
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        except sr.UnknownValueError:
            print("Google STT: no se pudo entender el audio")
            return None
        except sr.RequestError as e:
            print(f"Google STT: error de conexión: {e}")
            return None
        except Exception as e:
            print(f"Error en Google STT: {e}")
            return None

    def cleanup(self):
        self._whisper_model = None
        self._recognizer = None
