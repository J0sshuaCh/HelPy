# HelPy

**Asistente de voz con transcripción en tiempo real y LLM local/cloud.**

Aplicación de escritorio con interfaz PyQt5 que captura audio desde micrófono y/o sistema, transcribe a texto en tiempo real mediante Google Speech Recognition, y envía el texto a un LLM para obtener respuestas. Soporta múltiples proveedores: Google Gemini, Groq, LM Studio y modelos GGUF locales vía llama.cpp.

## Capturas

<img width="1919" height="1030" alt="image" src="https://github.com/user-attachments/assets/7c73df11-343c-4822-967a-7729941bcfb7" />


## Características

- **Transcripción en tiempo real dual**: captura simultánea o independiente de micrófono y loopback del sistema (audio interno/altavoces) con medidor de nivel VU en vivo.
- **Múltiples motores STT**: Google Speech Recognition y Whisper local (`tiny`, `base`, `small`, etc.).
- **Proveedores LLM flexibles**: Google Gemini, Groq, LM Studio (OpenAI-compatible) y modelos GGUF locales vía llama.cpp.
- **Ventana overlay moderna**: siempre visible (always-on-top), sin bordes, arrastrable, con soporte de modo compacto y animación colapsable suave.
- **Visor de guiones / Teleprompter**:
  - Compatible con archivos Markdown (`.md`), PDF (`.pdf`) y texto (`.txt`).
  - Control de zoom, opacidad regulable y búsqueda no destructiva de texto.
  - Autoscroll automático con control de velocidad por pasos y guía de lectura.
- **Accesibilidad universal (A11y)**: soporte para lectores de pantalla con etiquetas accesibles en todos los controles e indicadores de foco visuales de alto contraste (WCAG).
- **Temas visuales dinámicos**: selector de temas con filtrado por modo (Oscuro, Claro y Clásico) adaptados para alto contraste y ergonomía visual.
- **Atajos de teclado configurables**: atajos globales del sistema (grabación, envío a IA, colapso) y atajos rápidos de portapapeles y exportación.
- **Bandeja del sistema**: icono en bandeja con menú contextual para control rápido.

## Requisitos

- Windows 10/11 (probado) o Linux/macOS
- Python 3.10 o superior
- Micrófono funcional y/o dispositivo de loopback de audio
- Opcional: API keys para Google Gemini (`GOOGLE_API_KEY`) o Groq (`GROQ_API_KEY`)

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/J0sshuaCh/HelPy.git
cd HelPy

# Instalar dependencias en entorno virtual (.venv automático)
.\scripts\install.ps1   # Windows PowerShell
# o
bash scripts/install.sh  # Unix/macOS
```

## Configuración

Copia `.env.template` como `.env` y completa tus API keys si utilizas proveedores en la nube:

```env
GOOGLE_API_KEY="tu-api-key-de-gemini"
GROQ_API_KEY="tu-api-key-de-groq"
```

También puedes configurar proveedores (LLM y STT), modelos y preferencias directamente desde el **Diálogo de Preferencias** o en el asistente de inicio rápido (**Onboarding**).

Para ejecutar modelos locales GGUF (llama.cpp):

```bash
python scripts/download_model.py
```

## Uso

Inicia la aplicación con los scripts de ejecución:

```bash
.\scripts\run.ps1    # Windows
# o
bash scripts/run.sh  # Unix/macOS
```

O directamente mediante el módulo de Python:

```bash
python -m app.main
```

### Atajos y Controles

#### Atajos Globales (Sistema)
| Acción | Atajo por defecto | Descripción |
|--------|------------------|-------------|
| **Grabar / Detener** | `AltGr + G` | Alterna la captura de audio en vivo |
| **Enviar a IA** | `AltGr + \` | Envía el búfer de transcripción al LLM seleccionado |
| **Colapsar / Expandir** | `AltGr + H` | Alterna el modo compacto del overlay |

*Nota: Estos atajos globales se pueden personalizar desde el panel de Preferencias.*

#### Acciones Rápidas en Overlay
| Acción | Atajo / Control |
|--------|----------------|
| **Copiar transcripción** | `Ctrl + Shift + T` o botón copiar |
| **Copiar respuesta LLM** | `Ctrl + Shift + L` o botón copiar |
| **Exportar conversación** | `Ctrl + Shift + E` o botón guardar |
| **Arrastrar ventana** | Clic y arrastrar desde el encabezado |

#### Visor de Guiones (Teleprompter)
| Acción | Atajo / Control |
|--------|----------------|
| **Zoom in / out** | `Ctrl + Rueda del mouse` |
| **Buscar texto** | Barra de búsqueda integrada |
| **Autoscroll** | Botón Play/Pausa de autoscroll con ajuste de velocidad |

## Arquitectura

```
app/
├── main.py                          — Punto de entrada (QApplication)
├── core/
│   ├── assistant_controller.py       — Coordinador de captura, transcripción y LLM
│   ├── inference_server.py           — Servidor Flask para inferencia local GGUF
│   ├── llm_client.py                 — Cliente multi-proveedor LLM (Google, Groq, LM Studio, Local)
│   └── startup_validator.py          — Validador de configuración previa al arranque
├── ui/
│   ├── overlay_window/               — Ventana overlay del asistente
│   │   ├── preferences_dialog.py     — Panel flotante de configuración y atajos
│   │   ├── hotkeys.py, tray.py ...
│   │   └── ui/                       — Subcomponentes (grabación, displays de texto, controles)
│   ├── script_window/                — Visor de guiones/teleprompter
│   │   ├── file_loader.py, zoom.py, autoscroll.py, search_bar.py ...
│   │   └── ui/                       — Header, Toolbar y visores (Markdown, TXT, PDF)
│   ├── onboarding_dialog.py          — Asistente de bienvenida y primera configuración
│   ├── shared/                       — Componentes compartidos (VU meter, atajos, animaciones, iconos)
│   └── themes.py                     — Paletas de diseño y generación dinámica QSS
├── utils/
│   ├── dual_channel_transcriber.py   — Captura de micrófono y sistema con VAD
│   ├── logger.py                     — Logging estructurado
│   └── path_utils.py                 — Resolución de rutas multiplataforma y portables
└── assets/icons/                     — Iconos vectoriales SVG y logos del sistema
```

## Proveedores LLM

| Proveedor | Tipo | Requiere API key | Modelos sugeridos |
|-----------|------|-----------------|-------------------|
| **Google Gemini** | Cloud | Sí (`GOOGLE_API_KEY`) | `gemini-2.5-flash`, `gemini-1.5-flash` |
| **Groq** | Cloud | Sí (`GROQ_API_KEY`) | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` |
| **LM Studio** | Local (API) | No (opcional) | Cualquier modelo cargado localmente |
| **Local (llama.cpp)** | Local (GGUF) | No | Modelos GGUF compatibles |

## Construir Ejecutable

Genera una versión portable empaquetada mediante PyInstaller:

```powershell
.\scripts\build.ps1
```

El binario compilado se ubicará en `dist/HelPy/HelPy.exe`.

## Licencia

Distribuido bajo la licencia [MIT](LICENSE).
