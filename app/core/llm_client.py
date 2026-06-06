import json
import re
import subprocess
import time
import socket
import os
import requests
import sys
from pathlib import Path
from openai import OpenAI

# Singleton instance
_instance = None

class LlmClient:
    def __init__(self):
        self.provider = None
        self.client = None
        self.model_id = None
        self._inference_process = None
        self._inference_port = None
        self.reload()

    def _get_config_path(self):
        base = Path(__file__).resolve().parents[1] / "config"
        return base / "config.json"

    def _find_free_port(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

    def _stop_inference_server(self):
        if self._inference_process:
            try:
                self._inference_process.terminate()
                self._inference_process.wait(timeout=5)
            except:
                try:
                    self._inference_process.kill()
                except:
                    pass
            self._inference_process = None
            self._inference_port = None

    def reload(self):
        self._stop_inference_server()
        
        path = self._get_config_path()
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as handle:
                config = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return

        self.provider = config.get("provider", "LM Studio")
        api_key = config.get("api_key")
        model_id = config.get("model_id")
        self.model_id = model_id

        if self.provider == "LM Studio":
            base_url = config.get("base_url", "http://localhost:1234/v1")
            self.client = OpenAI(base_url=base_url, api_key=api_key or "lm-studio")
        elif self.provider == "Google":
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except ImportError:
                self.client = None
        elif self.provider == "Groq":
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
            except ImportError:
                self.client = None
        elif self.provider == "Local":
            self._start_local_server(model_id)
        else:
            self.client = None

    def _start_local_server(self, model_id):
        if not model_id:
            return

        model_path = Path(model_id)
        if not model_path.is_absolute():
            model_path = Path(__file__).resolve().parents[2] / model_path

        if not model_path.exists():
            self._local_error = f"No se encuentra el modelo en: {model_path}"
            return

        # Intentamos usar un puerto fijo primero para consistencia en debug
        self._inference_port = 5555
        server_script = Path(__file__).resolve().parent / "inference_server.py"
        log_path = Path(__file__).resolve().parents[2] / "inference_server.log"
        
        # Forzamos el uso del python del entorno virtual (.venv)
        root_dir = Path(__file__).resolve().parents[2]
        if os.name == 'nt':
            python_exe = str(root_dir / ".venv" / "Scripts" / "python.exe")
        else:
            python_exe = str(root_dir / ".venv" / "bin" / "python")

        # Fallback si por alguna razon no existe en esa ruta
        if not os.path.exists(python_exe):
            python_exe = sys.executable

        print(f"Lanzando servidor de inferencia con: {python_exe}")
        
        try:
            # Abrimos el log en modo append
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n--- INICIO SERVIDOR {time.ctime()} ---\n")
                self._inference_process = subprocess.Popen(
                    [python_exe, str(server_script), "--model_path", str(model_path), "--port", str(self._inference_port)],
                    stdout=log_file,
                    stderr=log_file,
                    cwd=str(root_dir),
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            
            # Wait for server to be ready
            max_retries = 45 
            for i in range(max_retries):
                if self._inference_process.poll() is not None:
                    # Si el proceso murio, leemos el final del log
                    if log_path.exists():
                        with open(log_path, "r", encoding="utf-8") as f:
                            last_lines = f.readlines()[-5:]
                            self._local_error = f"Servidor murio. Ultimos logs: {' '.join(last_lines)}"
                    else:
                        self._local_error = "El servidor de inferencia se cerro inesperadamente."
                    return

                try:
                    resp = requests.get(f"http://127.0.0.1:{self._inference_port}/health", timeout=1)
                    if resp.status_code == 200 and resp.json().get("loaded"):
                        print(f"Servidor listo en puerto {self._inference_port}.")
                        return
                except:
                    pass
                time.sleep(1)
            
            self._local_error = "Timeout: El servidor no respondio en 45s."
        except Exception as e:
            self._local_error = f"Error al lanzar el subproceso: {e}"

    def ask(self, prompt: str) -> str:
        system_prompt = "Eres un asistente virtual util, amigable y que responde en espanol de forma concisa."

        if self.provider == "Local":
            if not self._inference_port:
                err = getattr(self, '_local_error', 'No inicializado')
                return f"Error Local: {err}"
            
            try:
                resp = requests.post(
                    f"http://127.0.0.1:{self._inference_port}/ask",
                    json={"prompt": prompt, "system_prompt": system_prompt},
                    timeout=120
                )
                if resp.status_code == 200:
                    return resp.json().get("response", "")
                else:
                    return f"Error en servidor local: {resp.json().get('error', 'Unknown')}"
            except Exception as e:
                return f"Error de comunicacion con el modelo local: {e}"

        if not self.client or not self.model_id:
            return "Error: El cliente de IA no está configurado."

        try:
            if self.provider == "LM Studio" or self.provider == "Groq":
                respuesta = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                )
                return respuesta.choices[0].message.content
            elif self.provider == "Google":
                # Assuming simplified usage of google-genai
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=f"{system_prompt}\n\nUsuario: {prompt}",
                )
                return getattr(response, "text", "")
            return "Proveedor no soportado."
        except Exception as e:
            return f"Error conectando con el proveedor de IA: {e}"

    def __del__(self):
        self._stop_inference_server()

def get_llm_client():
    global _instance
    if _instance is None:
        _instance = LlmClient()
    return _instance
