# AYUDIN — Instrucciones de instalación y ejecución

Instrucciones para clonar, instalar dependencias y ejecutar el proyecto en Unix/macOS y Windows.

Requisitos
- Python 3.8 o superior instalado y disponible en PATH (python o python3).
- git para clonar el repositorio.

Clonar el repositorio
1. git clone <repo-url>
2. cd <repo-directory>

Unix / macOS
1. Instalar dependencias y crear un virtualenv:
   bash scripts/install.sh
2. Ejecutar la aplicación:
   bash scripts/run.sh

Notas:
- install.sh crea .venv en la raíz del proyecto y ejecuta pip install -r requirements.txt.
- run.sh activará .venv si existe. Si no existe, llamará a install.sh para crearla e instalar las dependencias.

Windows (PowerShell)
1. Instalar dependencias y crear un virtualenv (ejecutar en PowerShell):
   .\scripts\install.ps1
2. Ejecutar la aplicación:
   .\scripts\run.ps1

Notas:
- install.ps1 crea .venv en la raíz del proyecto y ejecuta pip install -r requirements.txt.
- run.ps1 activará .venv si existe. Si no existe, llamará a install.ps1 para crearla e instalar las dependencias.

## Instalación de Modelos
Este proyecto requiere el modelo Gemma 3 (GGUF), que no se incluye en el repositorio por su tamaño.

Para descargarlo automáticamente:
```bash
python download_model.py
```
*(Requiere la librería `huggingface_hub`)*

---

## Consejos
- Si usas un gestor de entornos diferente (conda, pipx), puedes usarlo en lugar de los scripts.
- Si tu sistema tiene varias versiones de Python, asegúrate que la que se usa sea 3.8 o superior.
- Para problemas con PyAudio en Windows, instala las ruedas (wheels) específicas para tu versión de Python/arquitectura si pip falla.

¿Quieres que también añada un comando npm-style (por ejemplo un script en package.json) o que los scripts comprueben la versión mínima de Python? Dime y lo añado.
