import yaml
from typing import Any, Dict, List
from pathlib import Path
from prance import ResolvingParser


class OpenApiParser:
    """
    OpenAPI 3.x / Swagger 2.0 Parser

    Produit une spécification simplifiée destinée à l'IA
    qui générera ensuite le scénario JMeter.
    """

    HTTP_METHODS = {
        "get",
        "post",
        "put",
        "delete",
        "patch",
        "head",
        "options",
    }

    # =========================================================

    def parse(self, spec_path: str | Path) -> dict:
        spec_path = Path(spec_path)

        if not spec_path.exists():
            raise ValueError(f"Fichier introuvable : {spec_path}")
        
        try:
            print(spec_path.read_text(encoding="utf-8")[:500])
            parser = ResolvingParser(
                str(spec_path),
                lazy=False
            )
        except Exception as exc:
            raise ValueError(
                f"Le fichier OpenAPI est invalide.\n\n"
                 + str(exc)

            ) from exc

        data = parser.specification

        if not isinstance(data, dict):
            raise ValueError("OpenAPI vide.")

        specification = {
            "title": "",
            "version": "",
            "description": "",
            "baseUrl": self._extract_base_url(data),
            "security": data.get("security", []),
            "endpoints": []
        }

        info = data.get("info", {})
        specification["title"] = info.get("title", "")
        specification["version"] = info.get("version", "")
        specification["description"] = info.get("description", "")

        paths = data.get("paths", {})
        for path, operations in paths.items():
            if not isinstance(operations, dict):
                continue

            for method, operation in operations.items():
                if method.lower() not in self.HTTP_METHODS:
                    continue

                endpoint = {
                    "method": method.upper(),
                    "path": path,
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "operationId": operation.get("operationId", ""),
                    "tags": operation.get("tags", []),
                    "parameters": self._parse_parameters(
                        operation.get("parameters", [])
                    ),
                    "pathValues": self._extract_path_values(
                        operation.get("parameters", [])
                    ),
                    "requestBody": self._parse_request_body(
                        operation.get("requestBody")
                    ),
                    "responses": self._parse_responses(
                        operation.get("responses", {})
                    ),
                    "security": operation.get(
                        "security",
                        specification["security"]
                    )
                }

                specification["endpoints"].append(endpoint)

        if not specification["endpoints"]:
            raise ValueError("Aucun endpoint trouvé.")

        return specification

    # =========================================================

    @staticmethod
    def _extract_base_url(data: dict):
        print("="*80)
        print(data.get("servers"))
        print("="*80)

        servers = data.get("servers")

        if isinstance(servers, list):

            if servers:

                url = servers[0].get("url")

                if url:
                    return url

        host = data.get("host")

        if host:

            schemes = data.get("schemes", ["http"])

            base = data.get("basePath", "")

            return f"{schemes[0]}://{host}{base}"

        return ""

    # =========================================================

    def _parse_parameters(self, parameters: List[dict]):

        result = []

        for p in parameters:

            if not isinstance(p, dict):
                continue

            schema = p.get("schema", {})

            result.append({

                "name": p.get("name"),

                "in": p.get("in"),

                "required": p.get("required", False),

                "description": p.get("description", ""),

                "type": schema.get("type"),

                "format": schema.get("format"),

                "default": schema.get("default"),

                "example": p.get(
                    "example",
                    schema.get("example")
                )

            })

        return result

    # =========================================================

    def _extract_path_values(self, parameters: List[dict]) -> Dict[str, Any]:
        """
        Extrait, pour chaque paramètre de type 'path', une valeur
        concrète utilisable directement dans l'URL (example, default,
        ou valeur générée selon le type).

        Exemple :
            /pet/{petId}  ->  {"petId": 12}
        """

        values: Dict[str, Any] = {}

        for p in parameters:

            if not isinstance(p, dict):
                continue

            if p.get("in") != "path":
                continue

            name = p.get("name")

            if not name:
                continue

            schema = p.get("schema", {})

            example = (
                p.get("example")
                if p.get("example") is not None
                else schema.get("example")
            )

            if example is None:
                example = schema.get("default")

            if example is None:
                param_type = schema.get("type")

                if param_type == "integer":
                    example = 1
                elif param_type == "number":
                    example = 1
                elif param_type == "boolean":
                    example = True
                elif param_type == "array":
                    example = []
                else:
                    example = "sample"

            values[name] = example

        return values

    # =========================================================

    def _parse_request_body(self, body):

        if not body:
            return None

        content = body.get("content", {})

        result = {}

        for media, value in content.items():

            schema = value.get("schema", {})

            result[media] = {

                "schema": schema,

                "example": value.get("example"),

                "examples": value.get("examples", {})

            }

        return result

    # =========================================================

    def _parse_responses(self, responses):

        parsed = {}

        for code, value in responses.items():

            if not isinstance(value, dict):
                continue

            parsed[str(code)] = {

                "description": value.get("description", ""),

                "content": {}

            }

            content = value.get("content", {})

            for media, media_data in content.items():

                parsed[str(code)]["content"][media] = {

                    "schema": media_data.get("schema", {}),

                    "example": media_data.get("example"),

                    "examples": media_data.get("examples", {})

                }

        return parsed