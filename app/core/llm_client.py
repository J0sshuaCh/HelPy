import json
import subprocess
import time
import socket
import os
import sys
import requests
from pathlib import Path
from typing import Optional

from openai import OpenAI

from app.utils.path_utils import resource_path, writable_config_path

_instance = None

class LlmClient:
    def __init__(self):
        self.provider: Optional[str] = None
        self.client = None
        self.model_id: Optional[str] = None
        self._context_text: str = ""
        self._inference_process = None
        self._inference_port = None
        self._local_error: Optional[str] = None
        self.reload()

    def _get_config_path(self) -> Path:
        return Path(writable_config_path("config.json"))

    def _resolve_model_path(self, model_id: str) -> Path:
        model_path = Path(model_id)
        if not model_path.is_absolute():
            model_path = Path(resource_path(model_id))
        return model_path

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
        api_key = config.get("api_key", "").strip()
        model_id = config.get("model_id", "").strip()
        self.model_id = model_id or None

        if self.provider == "LM Studio":
            base_url = config.get("base_url", "http://localhost:1234/v1")
            self.client = OpenAI(base_url=base_url, api_key=api_key or "lm-studio")
        elif self.provider == "Google":
            try:
                from google import genai
                if not api_key:
                    self.client = None
                else:
                    self.client = genai.Client(api_key=api_key)
            except (ImportError, ValueError):
                self.client = None
        elif self.provider == "Groq":
            try:
                from groq import Groq
                kwargs = {"api_key": api_key}
                if getattr(sys, 'frozen', False):
                    try:
                        import httpx
                        import certifi
                        kwargs["http_client"] = httpx.Client(
                            verify=certifi.where()
                        )
                    except ImportError:
                        pass
                self.client = Groq(**kwargs)
            except ImportError:
                self.client = None
        elif self.provider == "Local":
            self._start_local_server(model_id)
        else:
            self.client = None

    def _start_local_server(self, model_id: Optional[str]):
        if not model_id:
            return

        self._local_error = None

        model_path = self._resolve_model_path(model_id)
        if not model_path.exists():
            self._local_error = f"No se encuentra el modelo en: {model_path}"
            return

        self._inference_port = 5555
        
        # En PyInstaller, el servidor es un ejecutable separado
        if getattr(sys, 'frozen', False):
            # En modo onedir, el servidor está dentro del bundle dist/AYUDIN/
            executable = Path(sys._MEIPASS).parent / "inference_server.exe"
            cmd = [str(executable)]
        else:
            # En desarrollo, usamos el script python
            python_exe = sys.executable
            server_script = Path(__file__).resolve().parent / "inference_server.py"
            cmd = [python_exe, str(server_script)]

        cmd.extend(["--model_path", str(model_path), "--port", str(self._inference_port)])
        
        try:
            self._inference_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait for server
            for i in range(45):
                try:
                    resp = requests.get(f"http://127.0.0.1:{self._inference_port}/health", timeout=1)
                    if resp.status_code == 200 and resp.json().get("loaded"):
                        return
                except: pass
                time.sleep(1)
            
            self._local_error = "Timeout: El servidor no respondio"
        except Exception as e:
            self._local_error = f"Error al lanzar el subproceso: {e}"

    def set_context(self, text: str):
        self._context_text = text

    def clear_context(self):
        self._context_text = ""

    def has_context(self) -> bool:
        return bool(self._context_text)

    def _build_prompt(self, prompt: str) -> str:
        if self._context_text:
            return (
                f"Contexto de referencia:\n{self._context_text}\n\n"
                f"Pregunta:\n{prompt}"
            )
        return prompt

    def ask(self, prompt: str) -> str:
        system_prompt = (
            "Eres un asistente virtual util, amigable y que responde en espanol de forma concisa."
            if not self._context_text
            else "Eres un asistente virtual que responde preguntas en espanol de forma concisa. Usa el contexto proporcionado como guia para mantener las respuestas relacionadas al tema, pero puedes usar tu propio conocimiento para responder."
        )
        actual_prompt = self._build_prompt(prompt)

        if self.provider == "Local":
            if not self._inference_port:
                return f"Error Local: {self._local_error or 'No inicializado'}"
            try:
                resp = requests.post(
                    f"http://127.0.0.1:{self._inference_port}/ask",
                    json={"prompt": actual_prompt, "system_prompt": system_prompt},
                    timeout=120
                )
                if resp.status_code == 200:
                    return resp.json().get("response", "")
                return "Error en servidor local"
            except Exception as e:
                return f"Error: {e}"

        if not self.client or not self.model_id:
            return "Error: El cliente de IA no esta configurado."

        try:
            if self.provider in ("LM Studio", "Groq"):
                respuesta = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": actual_prompt},
                    ],
                    temperature=0.7,
                )
                return respuesta.choices[0].message.content
            elif self.provider == "Google":
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=f"{system_prompt}\n\nUsuario: {actual_prompt}",
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
        try:
            _instance = LlmClient()
        except Exception:
            _instance = LlmClient.__new__(LlmClient)
            _instance.provider = None
            _instance.client = None
            _instance.model_id = None
            _instance._context_text = ""
            _instance._inference_process = None
            _instance._inference_port = None
            _instance._local_error = "Error de inicialización"
    return _instance
