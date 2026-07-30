import os

from dotenv import load_dotenv
from groq import Groq, GroqError

from prompts.system_prompt import SYSTEM_PROMPT

load_dotenv()


class GroqClient:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY manquant. Renseignez-le dans le fichier .env "
                "(voir .env.example)."
            )

        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
        except GroqError as exc:
            raise RuntimeError(f"Échec de l'appel au modèle IA (Groq) : {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Le modèle IA a renvoyé une réponse vide.")

        return content
