from openai import OpenAI

# Conectamos el cliente al servidor LOCAL de LM Studio
# Nota: Asegúrate de que LM Studio esté corriendo con el servidor local activo en el puerto 1234
cliente_local = OpenAI(
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio" # Requerido pero no validado localmente
)

def pensar_respuesta(texto_usuario: str) -> str:
    if not texto_usuario:
        return "No te he escuchado bien."

    print(f"Enviando a LM Studio: {texto_usuario}")
    try:
        respuesta = cliente_local.chat.completions.create(
            model="local-model", # Usará el modelo cargado en LM Studio
            messages=[
                {"role": "system", "content": "Eres un asistente virtual útil, amigable y que responde en español de forma concisa."},
                {"role": "user", "content": texto_usuario}
            ],
            temperature=0.7
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        return f"Error conectando con LM Studio: {e}. Asegúrate de que el servidor esté encendido."
