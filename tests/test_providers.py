#!/usr/bin/env python3
"""Integration test for all LLM providers.

Usage:
    python tests/test_providers.py                    # test all providers
    python tests/test_providers.py --provider google   # test one provider

Requires environment variables (or .env file):
    GOOGLE_API_KEY   for Google Gemini
    GROQ_API_KEY     for Groq
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.core.llm_client import get_llm_client
from app.utils.path_utils import writable_config_path, resource_path


CONFIG_PATH = Path(writable_config_path("config.json"))
_original_config: str = ""


def _save_config() -> str:
    global _original_config
    _original_config = CONFIG_PATH.read_text(encoding="utf-8") if CONFIG_PATH.exists() else ""
    return _original_config


def _restore_config(content: str):
    if content:
        CONFIG_PATH.write_text(content, encoding="utf-8")
    elif CONFIG_PATH.exists():
        CONFIG_PATH.unlink()

    if not content:
        return
    try:
        cfg = json.loads(content)
        if cfg.get("provider") == "Local":
            import llama_cpp
    except (json.JSONDecodeError, ImportError):
        return
    get_llm_client().reload()


def _write_config(provider: str, api_key: str, model_id: str):
    data = {"provider": provider, "api_key": api_key, "model_id": model_id}
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    get_llm_client().reload()


def test_lm_studio():
    base = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
    print(f"\n[LM Studio]  {base} ...")
    try:
        requests.get(f"{base}/models", timeout=3)
    except requests.RequestException:
        print(f"  [SKIP] servidor no disponible en {base}")
        return None

    api_key = os.environ.get("LMSTUDIO_API_KEY") or os.environ.get("LM_API_TOKEN", "")
    model_id = os.environ.get("LMSTUDIO_MODEL") or os.environ.get("SLMSTUDIO_MODEL", "gpt-3.5-turbo")
    _write_config("LM Studio", api_key, model_id)
    result = get_llm_client().ask("Decime exactamente: 'OK'")
    if result and not result.startswith("Error"):
        print(f"  [OK] \"{result[:80]}\"")
        return True
    print(f"  [FAIL] {result[:120]}")
    return False


def test_google():
    print(f"\n[Google] ...")
    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not api_key:
        print(f"  [SKIP] variable GOOGLE_API_KEY no seteada")
        return None
    print(f"  API key: {api_key[:6]}...{api_key[-4:]}")
    _write_config("Google", api_key, "gemini-3.1-flash-lite")
    result = get_llm_client().ask("Decime exactamente: 'OK'")
    if result and not result.startswith("Error"):
        print(f"  [OK] \"{result[:80]}\"")
        return True
    print(f"  [FAIL] {result[:120]}")
    return False


def test_groq():
    print(f"\n[Groq] ...")
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print(f"  [SKIP] variable GROQ_API_KEY no seteada")
        return None
    print(f"  API key: {api_key[:6]}...{api_key[-4:]}")
    _write_config("Groq", api_key, "openai/gpt-oss-120b")
    result = get_llm_client().ask("Decime exactamente: 'OK'")
    if result and not result.startswith("Error"):
        print(f"  [OK] \"{result[:80]}\"")
        return True
    print(f"  [FAIL] {result[:120]}")
    return False


def test_local():
    print(f"\n[Local] ...")
    try:
        import llama_cpp
    except ImportError:
        print(f"  [SKIP] llama_cpp no instalado")
        return None

    try:
        orig = json.loads(_original_config) if _original_config else {}
    except json.JSONDecodeError:
        orig = {}

    model_id = orig.get("model_id", "models/gemma-3-1b-it-Q4_K_M.gguf")
    model_path = Path(model_id)
    if not model_path.is_absolute():
        model_path = Path(resource_path(model_id))

    print(f"  Modelo: {model_path}")
    if not model_path.exists():
        print(f"  [SKIP] archivo no encontrado")
        return None
    print(f"  Iniciando servidor local...")

    _write_config("Local", "", str(model_path))
    result = get_llm_client().ask("Decime exactamente: 'OK'")
    if result and not result.startswith("Error"):
        print(f"  [OK] \"{result[:80]}\"")
        return True
    print(f"  [FAIL] {result[:120]}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Test de proveedores LLM de HelPy")
    parser.add_argument(
        "--provider",
        choices=["all", "lmstudio", "google", "groq", "local"],
        default="all",
    )
    args = parser.parse_args()

    print("=== Test de Proveedores LLM ===")
    print()

    original = _save_config()

    tests = {
        "lmstudio": test_lm_studio,
        "google": test_google,
        "groq": test_groq,
        "local": test_local,
    }

    results = {}
    try:
        if args.provider == "all":
            for name, func in tests.items():
                results[name] = func()
                time.sleep(1)
        else:
            results[args.provider] = tests[args.provider]()
    finally:
        _restore_config(original)

    print(f"\n=== Resumen ===")
    passed = sum(1 for v in results.values() if v is True)
    skipped = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)
    print(f"  [OK]   Pasaron:  {passed}")
    print(f"  [SKIP] Saltados: {skipped}")
    print(f"  [FAIL] Fallaron: {failed}")
    print(f"  Total: {total}")
    print()
    print("Config original restaurada.")


if __name__ == "__main__":
    main()
