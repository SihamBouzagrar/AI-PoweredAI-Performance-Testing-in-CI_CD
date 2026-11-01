
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
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],
                temperature=0.2,
                max_tokens=4096,
            )

        except GroqError as exc:
            raise RuntimeError(
                f"Échec de l'appel au modèle IA (Groq) : {exc}"
            ) from exc

        if not response.choices:
            raise RuntimeError(
                "Groq n'a retourné aucun choix de réponse."
            )

        choice = response.choices[0]
        content = choice.message.content

        if not content or not content.strip():
            raise RuntimeError(
                "Le modèle IA a renvoyé une réponse vide. "
                f"finish_reason={choice.finish_reason}, "
                f"usage={response.usage}"
            )

        return content.strip()
