import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tu_proyecto_ai'))

from core.ai_assistant import AIAssistant
from threading import Event
import time

done = Event()
result = [None]

def on_result(text):
    result[0] = text
    done.set()

def on_status(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

assistant = AIAssistant()
assistant.on_result(on_result)
assistant.on_status(on_status)

print("Grabando 3 segundos de audio del sistema...")
assistant.start_recording()

for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

print("Transcribiendo...")
assistant.stop_recording_and_transcribe()

if done.wait(timeout=120):
    print(f"\nTexto transcrito: '{result[0]}'")
else:
    print("\nLa transcripción no completó a tiempo")

assistant.cleanup()
