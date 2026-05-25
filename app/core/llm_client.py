from openai import OpenAI


class LlmClient:
    def __init__(self):
        self.client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="sk-lm-hRnxNXRM:630LLCj0ze3Px7xdcCc6",
        )

    def ask(self, prompt: str) -> str:
        try:
            respuesta = self.client.chat.completions.create(
                model="local-model",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente virtual util, amigable y que responde en espanol de forma concisa.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
            contenido = respuesta.choices[0].message.content
            if contenido:
                return contenido
        except Exception:
            pass

        try:
            respuesta = self.client.completions.create(
                model="local-model",
                prompt=prompt,
                temperature=0.7,
                max_tokens=512,
            )
            texto = respuesta.choices[0].text
            return texto.strip() if texto else ""
        except Exception as e:
            return f"Error conectando con LM Studio: {e}"
