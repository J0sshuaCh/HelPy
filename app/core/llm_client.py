import os

from openai import OpenAI


class LlmClient:
    def __init__(self):
        # If you're using a local OpenAI-compatible server (e.g. LM Studio), the API key
        # can be any non-empty string. Keep it out of source control regardless.
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LMSTUDIO_API_KEY")
        if not api_key:
            api_key = "local"  # safe default for local servers that ignore auth

        self.client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key=api_key,
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
            return respuesta.choices[0].message.content
        except Exception as e:
            return f"Error conectando con LM Studio: {e}"
