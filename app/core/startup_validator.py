"""
Módulo de validación de configuración al inicio.
Verifica API keys, dispositivos de audio y modelos locales.
"""
import os
import json
from pathlib import Path
from app.utils.path_utils import writable_config_path


def validate_startup():
    """
    Valida la configuración al iniciar la aplicación.
    Retorna una lista de tuplas (tipo, mensaje) donde tipo es 'error' o 'warning'.
    """
    issues = []
    
    # 1. Verificar config.json
    config_path = writable_config_path("config.json")
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            issues.append(("error", "Archivo de configuración corrupto"))
    else:
        issues.append(("warning", "No se encontró config.json - se usarán valores por defecto"))
    
    # 2. Verificar proveedor LLM y API key
    provider = config.get("provider", "LM Studio")
    api_key = config.get("api_key", "")
    model_id = config.get("model_id", "")
    
    if provider in ("Google", "Groq"):
        if not api_key or api_key.strip() == "":
            issues.append(("error", f"Falta API key para {provider}. Ve a Configurar LLM para agregarla."))
        elif len(api_key.strip()) < 10:
            issues.append(("warning", f"API key de {provider} parece muy corta. Verifica que sea correcta."))
    
    if provider == "Local":
        model_path = model_id
        if model_path:
            if not os.path.isabs(model_path):
                from app.utils.path_utils import resource_path
                model_path = resource_path(model_path)
            if not os.path.exists(model_path):
                issues.append(("warning", f"Modelo local no encontrado: {model_path}. Puedes descargarlo desde Configurar LLM."))
        else:
            issues.append(("warning", "Modo local seleccionado pero no se ha indicado ruta del modelo .gguf"))
    
    # 3. Verificar STT provider
    stt_provider = config.get("stt_provider", "google")
    whisper_model = config.get("whisper_model", "tiny")
    
    if stt_provider == "whisper":
        # Verificar que faster_whisper esté disponible
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            issues.append(("error", "faster-whisper no está instalado. Instala con: pip install faster-whisper"))
    
    # 4. Verificar dispositivos de audio
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        has_input = any(d.get("max_input_channels", 0) > 0 for d in devices)
        if not has_input:
            issues.append(("error", "No se detectó ningún micrófono disponible"))
    except Exception as e:
        issues.append(("warning", f"No se pudieron verificar dispositivos de audio: {e}"))
    
    return issues


def get_validation_summary(issues):
    """
    Retorna un resumen formateado de los problemas encontrados.
    """
    if not issues:
        return "[OK] Configuracion correcta"
    
    errors = [msg for tipo, msg in issues if tipo == "error"]
    warnings = [msg for tipo, msg in issues if tipo == "warning"]
    
    lines = []
    if errors:
        lines.append("ERRORES:")
        for e in errors:
            lines.append(f"  [X] {e}")
    if warnings:
        lines.append("ADVERTENCIAS:")
        for w in warnings:
            lines.append(f"  [!] {w}")
    
    return "\n".join(lines)
