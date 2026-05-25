import speech_recognition as sr

def escuchar_usuario() -> str:
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("Ajustando ruido...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Habla ahora...")
            audio = recognizer.listen(source)
    except Exception as e:
        return f"Error con el micrófono: {e}. ¿Tienes PyAudio instalado?"
        
    try:
        print("Transcribiendo con Google...")
        texto = recognizer.recognize_google(audio, language="es-ES")
        return texto
    except sr.UnknownValueError:
        return "" # Retorna vacío si no entiende
    except sr.RequestError as e:
        return f"Error de conexión: {e}"
