import queue
import time
import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel

def main():
    print("Inicializando modelos...")
    
    # 1. Configurar WebRTC VAD
    vad = webrtcvad.Vad(3) # Nivel más agresivo (0-3) para aislar la voz
    
    # 2. Configurar faster-whisper
    print("Cargando modelo Whisper 'tiny' (esto puede tomar un momento la primera vez)...")
    # compute_type="int8" reduce el uso de memoria a costa de mínima precisión
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("Modelo cargado.")
    
    # Parámetros estrictos para WebRTC VAD y Whisper
    SAMPLE_RATE = 16000
    CHANNELS = 1
    FRAME_DURATION_MS = 30
    FRAME_SIZE = int(SAMPLE_RATE * (FRAME_DURATION_MS / 1000.0)) # 480 frames
    
    # Variables de estado
    audio_queue = queue.Queue()
    speech_buffer = bytearray()
    is_speaking = False
    silence_frames = 0
    MAX_SILENCE_FRAMES = int(0.6 / (FRAME_DURATION_MS / 1000.0)) # 0.6 segundos de silencio
    
    print("\n[LISTO] Habla por el micrófono (Presiona Ctrl+C para salir)...")
    
    def callback(indata, frames, time_info, status):
        """Callback de sounddevice para capturar audio"""
        if status:
            print(status, flush=True)
        # Convertir a mono y a int16 (requerido por webrtcvad)
        audio = indata
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        audio_int16 = audio.astype(np.int16)
        
        # Enviar chunks exactos al queue
        audio_bytes = audio_int16.tobytes()
        audio_queue.put(audio_bytes)
        
    # Inicializar stream
    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype='int16',
            blocksize=FRAME_SIZE, # Pedir a sounddevice bloques exactos
            callback=callback
        )
        with stream:
            while True:
                # Leer del queue
                frame = audio_queue.get()
                
                # Para evitar problemas con tamaños incorrectos, aseguramos 30ms exactos
                if len(frame) != FRAME_SIZE * 2: 
                    continue

                # 1. Aplicar VAD al frame (requiere 16kHz, 16-bit mono)
                is_speech = vad.is_speech(frame, SAMPLE_RATE)
                
                if is_speech:
                    if not is_speaking:
                        print("\n[VAD] Detectando voz...", end="", flush=True)
                        is_speaking = True
                    speech_buffer.extend(frame)
                    silence_frames = 0
                else:
                    if is_speaking:
                        speech_buffer.extend(frame) # Añadir algo de silencio al final
                        silence_frames += 1
                        print(".", end="", flush=True)
                        
                        # Si acumulamos suficiente silencio, cortamos y transcribimos
                        if silence_frames >= MAX_SILENCE_FRAMES:
                            print("\n[VAD] Silencio detectado. Transcribiendo...")
                            
                            # Convertir bytearray a float32 numpy array para Whisper
                            audio_np = np.frombuffer(bytes(speech_buffer), dtype=np.int16).astype(np.float32) / 32768.0
                            
                            if len(audio_np) > SAMPLE_RATE * 0.5: # Ignorar fragmentos muy cortos (<0.5s)
                                start_time = time.time()
                                
                                # 2. Transcribir con faster-whisper
                                segments, info = model.transcribe(audio_np, language="es", beam_size=5)
                                text = " ".join([segment.text for segment in segments])
                                
                                elapsed = time.time() - start_time
                                print(f"[WHISPER] Texto ({elapsed:.2f}s): {text.strip()}")
                            else:
                                print("[WHISPER] Fragmento demasiado corto, ignorado.")
                                
                            # Reiniciar buffer
                            speech_buffer = bytearray()
                            is_speaking = False
                            silence_frames = 0
                            
    except KeyboardInterrupt:
        print("\nSaliendo...")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
