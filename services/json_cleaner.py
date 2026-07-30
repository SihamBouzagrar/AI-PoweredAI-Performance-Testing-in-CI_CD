import json
import re


class JsonCleaner:
    """Extracts a clean, parsable JSON object out of a raw LLM response,
    even if the model added markdown fences or stray prose around it."""

    def clean(self, response: str) -> dict:
        if not response or not response.strip():
            raise ValueError("Réponse vide reçue du modèle IA.")

        text = response.strip()
        text = text.replace("```json", "").replace("```", "")

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Fallback : extraire le premier objet JSON valide dans le texte
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Impossible de parser le JSON renvoyé par l'IA : {exc}"
                ) from exc

        raise ValueError("Aucun objet JSON trouvé dans la réponse de l'IA.")
