import sys
import argparse
import json
import logging
from flask import Flask, request, jsonify, Response, stream_with_context
from waitress import serve

# Desactivar logs innecesarios de Flask/Waitress
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

@app.route('/ask_stream', methods=['POST'])
def ask_stream():
    global llm
    if not llm:
        return jsonify({"error": "Modelo no cargado"}), 500

    data = request.json
    prompt = data.get("prompt", "")
    system_prompt = data.get("system_prompt", "Eres un asistente virtual útil y amigable.")

    def generate():
        try:
            stream = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=512,
                stream=True,
            )
            for chunk in stream:
                delta = chunk["choices"][0]["delta"]
                content = delta.get("content", "")
                if content:
                    yield f"data: {json.dumps({'token': content})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

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
        
        serve(app, host='127.0.0.1', port=args.port, _quiet=True)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
