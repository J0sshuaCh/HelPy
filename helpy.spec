# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

# Binarios de llama_cpp — resuelve la ruta dinámicamente donde sea que pip lo haya instalado
import llama_cpp
llama_lib_path = Path(llama_cpp.__file__).parent / "lib"
binaries = [
    (str(llama_lib_path / "ggml-base.dll"), "llama_cpp/lib"),
    (str(llama_lib_path / "ggml-cpu.dll"), "llama_cpp/lib"),
    (str(llama_lib_path / "ggml.dll"), "llama_cpp/lib"),
    (str(llama_lib_path / "llama.dll"), "llama_cpp/lib"),
    (str(llama_lib_path / "mtmd.dll"), "llama_cpp/lib"),
]

# Archivos compartidos
datas = [
    ("app/assets", "app/assets"),
    ("app/config/config_template.json", "app/config"),
]

# Hidden imports necesarios
hiddenimports = [
    "sounddevice",
    "soundcard",
    "llama_cpp",
    "llama_cpp.llama_cpp",
    "openai",
    "groq",
    "google.genai",
    "pynput",
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "fitz",
    "requests",
    "huggingface_hub",
    "dotenv",
    "speech_recognition",
    "ctypes",
    "certifi",
    "httpx",
    "httpcore",
    "ssl",
    "faster_whisper",
    "ctranslate2",
]

# 1. Análisis para HelPy (Main App)
a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['hooks'],
    excludes=[
        'tkinter', 'matplotlib', 'PIL', 'cv2',
        'torch', 'torchvision', 'torchaudio',
        'numba', 'scipy', 'pandas', 'sklearn',
        'tensorflow', 'jax', 'ray',
        'notebook', 'jupyter', 'ipython',
        'bokeh', 'plotly', 'dash',
        'onnxruntime',
    ],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HelPy',
    debug=False,
    console=False,
    icon=None,
)

# 2. Análisis para Inferencia (Subproceso)
a_server = Analysis(
    ['app/core/inference_server.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=['llama_cpp', 'flask', 'waitress'],
    excludes=[
        'tkinter', 'matplotlib', 'PIL', 'cv2',
        'torch', 'torchvision', 'torchaudio',
        'numba', 'scipy', 'pandas', 'sklearn',
        'tensorflow', 'jax', 'ray',
        'notebook', 'jupyter', 'ipython',
        'bokeh', 'plotly', 'dash',
        'onnxruntime',
    ],
    noarchive=False,
    cipher=block_cipher,
)
pyz_server = PYZ(a_server.pure, cipher=block_cipher)
exe_server = EXE(
    pyz_server,
    a_server.scripts,
    a_server.binaries,
    a_server.datas,
    [],
    name='inference_server',
    debug=False,
    console=False,
)

# 3. Collector (Juntar todo)
coll = COLLECT(
    exe,
    exe_server,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='HelPy',
)
