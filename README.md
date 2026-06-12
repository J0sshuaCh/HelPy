# AYUDIN (HelPy)

**Asistente de voz con transcripción en tiempo real y LLM local/cloud.**

Aplicación de escritorio con interfaz PyQt5 que captura audio desde micrófono y/o sistema, transcribe a texto en tiempo real mediante Google Speech Recognition, y envía el texto a un LLM para obtener respuestas. Soporta múltiples proveedores: Google Gemini, Groq, LM Studio y modelos GGUF locales vía llama.cpp.

## Capturas

*(Agrega capturas de pantalla aquí)*

## Características

- **Transcripción en tiempo real** — Captura dual micrófono + loopback del sistema simultáneamente
- **Múltiples proveedores LLM** — Google Gemini, Groq, LM Studio (OpenAI-compatible), llama.cpp local
- **Ventana overlay** — Siempre al frente, sin bordes, arrastrable, colapsable
- **Visor de guiones/scripts** — Carga archivos Markdown, PDF y TXT con zoom y opacidad
- **Temas visuales** — 8 temas: Slate Minimalist, Cyber Obsidian, Nordic Frost, Tokyo Night, Dark Earth, Dark Forest, Catppuccin Latte, Solarized Light
- **Atajos globales de teclado** — `AltGr + \` enviar a LLM, `AltGr + G` grabar, `AltGr + H` colapsar
- **Bandeja del sistema** — Icono en bandeja con menú contextual
- **Modo local sin conexión** — Usa modelos GGUF descargados localmente

## Requisitos

- Windows 10/11 (probado) o Linux/macOS
- Python 3.8 o superior
- Micrófono funcional (para captura de audio)
- Opcional: API keys para Google Gemini, Groq

## Instalación

```bash
# Clonar
git clone https://github.com/J0sshuaCh/HelPy.git
cd HelPy

# Instalar dependencias (crea .venv automáticamente)
.\scripts\install.ps1   # Windows PowerShell
# o
bash scripts/install.sh  # Unix/macOS
```

## Configuración

Copia `.env.template` como `.env` y completa las API keys:

```env
GOOGLE_API_KEY="tu-api-key-de-gemini"
GROQ_API_KEY="tu-api-key-de-groq"
```

Para modo local (llama.cpp), descarga el modelo:

```bash
python scripts/download_model.py
```

Selecciona el proveedor desde la interfaz o editando `app/config/config.json`.

## Uso

```bash
.\scripts\run.ps1    # Windows
bash scripts/run.sh  # Unix/macOS
```

O directamente:

```bash
python -m app.main
```

### Controles

| Acción | Atajo / Control |
|--------|----------------|
| Grabar / Detener | `AltGr + G` o botón Record |
| Enviar a LLM | `AltGr + \` o botón Send |
| Colapsar overlay | `AltGr + H` o botón colapsar |
| Zoom script | `Ctrl + Rueda del mouse` |
| Arrastrar ventana | Click + arrastrar en barra superior |

## Arquitectura

```
app/
├── main.py                          — Entry point (QApplication)
├── core/
│   ├── assistant_controller.py       — Orquestador transcripción + LLM
│   ├── inference_server.py           — Servidor Flask para GGUF local
│   └── llm_client.py                 — Cliente multi-proveedor (singleton)
├── ui/
│   ├── overlay_window/               — Ventana overlay del asistente
│   │   ├── window.py, tray.py, hotkeys.py ...
│   │   └── ui/                       — Subcomponentes (header, panels, etc.)
│   ├── script_window/                — Visor de guiones/scripts
│   │   ├── window.py, file_loader.py, zoom.py ...
│   │   └── ui/                       — Toolbar, viewers (text, PDF)
│   ├── shared/                       — Componentes compartidos
│   └── themes.py                     — Paletas de color + generación QSS
├── utils/
│   ├── dual_channel_transcriber.py   — Captura multi-hilo mic + sistema
│   └── path_utils.py                 — Resolución de rutas
└── assets/icons/                     — Iconos SVG
```

## Proveedores LLM

| Proveedor | Tipo | Requiere API key |
|-----------|------|-----------------|
| Google Gemini | Cloud | Sí (`GOOGLE_API_KEY`) |
| Groq | Cloud | Sí (`GROQ_API_KEY`) |
| LM Studio | Local (API) | No (opcional) |
| Local (llama.cpp) | Local (GPU/CPU) | No |

## Construir ejecutable

```powershell
.\scripts\build.ps1
```

Requiere PyInstaller. Genera `dist/AYUDIN/` con `AYUDIN.exe`.

## Licencia

MIT
