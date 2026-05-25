import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import threading
import time
from datetime import datetime
from typing import Optional, Callable


class SystemAudioRecorder:
    DEVICE_PRIORITY = ["mezcla estéreo", "mezcla estereo", "stereo mix",
                       "what u hear", "waveout", "rec."]

    def __init__(self, sample_rate: int = 16000, channels: int = 1,
                 output_dir: Optional[str] = None):
        self._requested_sr = sample_rate
        self.actual_sr = sample_rate
        self.channels = channels
        self.output_dir = output_dir or os.path.join(os.getcwd(), "recordings")
        os.makedirs(self.output_dir, exist_ok=True)

        self.recording = False
        self.stream = None
        self.frames: list[np.ndarray] = []
        self.device_id: Optional[int] = None
        self.selected_device_name: str = ""

        self._select_best_device()

    def _select_best_device(self):
        try:
            devices = sd.query_devices()
            hostapi = sd.query_hostapis()

            wasapi_idx = next(
                (i for i, ha in enumerate(hostapi)
                 if "wasapi" in ha["name"].lower()),
                None
            )

            candidates = []

            for idx, dev in enumerate(devices):
                name_lower = dev["name"].lower()
                if dev["max_input_channels"] < 1:
                    continue

                for kw in self.DEVICE_PRIORITY:
                    if kw in name_lower:
                        priority = -name_lower.index(kw)

                        has_stereo = "estéreo" in name_lower or "estereo" in name_lower
                        if has_stereo:
                            priority -= 10

                        is_wasapi = (wasapi_idx is not None
                                     and dev["hostapi"] == wasapi_idx)
                        if is_wasapi:
                            priority -= 5

                        candidates.append((priority, idx, dev["name"]))
                        break

            if candidates:
                candidates.sort(key=lambda x: x[0])
                _, self.device_id, self.selected_device_name = candidates[0]
                dev_info = devices[self.device_id]
                self.actual_sr = int(dev_info["default_samplerate"])
                print(f"Audio: usando '{self.selected_device_name}' (dispositivo {self.device_id}, {self.actual_sr} Hz)")
            else:
                default_input = sd.default.device[0]
                if default_input is None or default_input < 0:
                    input_devices = [(i, d) for i, d in enumerate(devices)
                                     if d["max_input_channels"] > 0]
                    if input_devices:
                        self.device_id = input_devices[0][0]
                        self.selected_device_name = input_devices[0][1]["name"]
                    else:
                        raise RuntimeError("No se encontró ningún dispositivo de entrada de audio")
                else:
                    self.device_id = default_input
                    self.selected_device_name = devices[self.device_id]["name"]

                print(f"Audio: usando dispositivo por defecto '{self.selected_device_name}'")

        except Exception as e:
            print(f"Error al seleccionar dispositivo de audio: {e}")
            raise

    def start_recording(self):
        if self.recording:
            return

        self.frames = []
        self.recording = True

        def callback(indata, frames, time_info, status):
            if status:
                print(f"Audio status: {status}")
            if self.recording:
                self.frames.append(indata.copy())

        try:
            self.stream = sd.InputStream(
                device=self.device_id,
                samplerate=self.actual_sr,
                channels=self.channels,
                callback=callback,
                blocksize=1024
            )
            self.stream.start()
            print("Grabación iniciada...")
        except Exception as e:
            self.recording = False
            print(f"Error al iniciar grabación: {e}")

    def stop_recording(self) -> Optional[str]:
        if not self.recording:
            return None

        self.recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.frames:
            print("No se capturó audio.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"audio_{timestamp}.wav")

        try:
            audio_data = np.concatenate(self.frames, axis=0)
            sf.write(filename, audio_data, self.actual_sr)
            print(f"Audio guardado: {filename}")
            return filename
        except Exception as e:
            print(f"Error al guardar audio: {e}")
            return None

    def get_audio_data(self) -> Optional[bytes]:
        if not self.frames:
            return None
        try:
            audio_data = np.concatenate(self.frames, axis=0)
            import io
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, self.actual_sr, format='WAV')
            return buffer.getvalue()
        except Exception as e:
            print(f"Error al obtener datos de audio: {e}")
            return None

    def get_audio_data_resampled(self, target_sr: int = 16000) -> Optional[bytes]:
        if not self.frames:
            return None
        try:
            audio_data = np.concatenate(self.frames, axis=0)
            if self.actual_sr != target_sr:
                import scipy.signal as signal
                ratio = target_sr / self.actual_sr
                new_len = int(len(audio_data) * ratio)
                audio_data = signal.resample(audio_data, new_len, axis=0)
            import io
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, target_sr, format='WAV')
            return buffer.getvalue()
        except ImportError:
            return self.get_audio_data()
        except Exception as e:
            print(f"Error al obtener datos de audio: {e}")
            return None

    def record_for_duration(self, duration: float) -> Optional[str]:
        self.start_recording()
        time.sleep(duration)
        return self.stop_recording()

    def cleanup(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.recording = False
