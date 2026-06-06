import sys
import argparse
import logging
from flask import Flask, request, jsonify
from waitress import serve

# Desactivar logs innecesarios de Flask/Waitress para no llenar el buffer de pipe
logging.getLogger('waitress').setLevel(logging.ERROR)

app = Flask(__name__)
llm = None

@app.route('/ask', methods=['POST'])
def ask():
    global llm
    if not llm:
        return jsonify({"error": "Modelo no cargado"}), 500
    
    data = request.json
    prompt = data.get("prompt", "")
    system_prompt = data.get("system_prompt", "Eres un asistente virtual útil y amigable.")
    
    try:
        respuesta = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=512,
        )
        content = respuesta["choices"][0]["message"]["content"]
        return jsonify({"response": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "loaded": llm is not None})

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--port", type=int, default=5555)
    args = parser.parse_args()

    print(f"Iniciando servidor en puerto {args.port}...")
    
    try:
        from llama_cpp import Llama
        print(f"Cargando modelo GGUF...")
        llm = Llama(
            model_path=args.model_path,
            n_ctx=4096,
            n_threads=None,
            verbose=False
        )
        print("Modelo cargado exitosamente.")
        
        # Usamos waitress en lugar de app.run() para evitar el Windows Error 6
        print(f"Servidor listo en http://localhost:{args.port}")
        serve(app, host='127.0.0.1', port=args.port, _quiet=True)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
