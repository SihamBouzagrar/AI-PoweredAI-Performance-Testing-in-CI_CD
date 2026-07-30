import json

SYSTEM_PROMPT = """
You are a Senior Performance Test Architect specialized in:

- Apache JMeter
- REST APIs
- OpenAPI 3.x
- Banking APIs
- Performance Engineering

Your mission is to generate a realistic Apache JMeter performance scenario.

Rules:

- Return ONLY valid JSON.
- Do NOT return Markdown.
- Do NOT use ```json.
- Do NOT explain anything.
- The JSON must be directly parsable with json.loads().
- Use ONLY endpoints present in the specification.
"""


class ScenarioPromptBuilder:

    def build(self, specification, analysis):

        compact_spec = self._compact_specification(specification)

        return f"""
{SYSTEM_PROMPT}

=========================
API ANALYSIS
=========================

Total endpoints: {analysis["totalEndpoints"]}

GET: {analysis["get"]}

POST: {analysis["post"]}

PUT: {analysis["put"]}

DELETE: {analysis["delete"]}

PATCH: {analysis["patch"]}

Authentication: {analysis["authentication"]}

Banking operations: {analysis["bankingOperations"]}

=========================
OPENAPI SUMMARY
=========================

{json.dumps(compact_spec, indent=2)}

=========================
TASK
=========================

Generate a realistic Apache JMeter performance scenario.

Automatically determine:

- threads
- rampUp
- loops
- thinkTimeMin
- thinkTimeMax
- business transactions
- assertions
- request weights

Use ONLY endpoints contained in the specification.

Each endpoint in the OPENAPI SUMMARY may contain a "pathValues" object,
mapping path parameter names (e.g. "petId" in "/pet/{{petId}}") to a
concrete sample value taken directly from the specification.

For every transaction you generate whose "path" contains a placeholder
like {{paramName}}, you MUST copy the corresponding "pathValues" object
EXACTLY as provided by the matching endpoint in the OPENAPI SUMMARY.

- Do NOT invent new path parameter values.
- Do NOT modify the values given in "pathValues".
- Do NOT rename the keys.
- If an endpoint has no "pathValues" (no path parameters), omit the
  field or return an empty object {{}}.

Return ONLY this JSON:

{{
  "configuration": {{
    "threads": 0,
    "rampUp": 0,
    "loops": 0,
    "thinkTimeMin": 0,
    "thinkTimeMax": 0
  }},
  "transactions": [
    {{
      "name": "",
      "method": "",
      "path": "",
      "weight": 0,
      "headers": {{}},
      "body": {{}},
      "pathValues": {{}}
    }}
  ],
  "assertions": [
    {{
      "path": "",
      "method": "",
      "expectedStatus": 200
    }}
  ]
}}

Rules:

- threads, rampUp and loops must be integers.
- thinkTimeMin < thinkTimeMax.
- weights should total approximately 100.
- expectedStatus must match documented responses.
- Do not invent endpoints.
- pathValues must always match the values given in the OPENAPI SUMMARY
  for the corresponding endpoint.
- Return ONLY the JSON object.
"""

    # ------------------------------------------------------------------

    def _compact_specification(self, specification):

        compact = {
            "title": specification.get("title"),
            "version": specification.get("version"),
            "baseUrl": specification.get("baseUrl"),
            "security": specification.get("security", []),
            "endpoints": [],
        }

        for ep in specification.get("endpoints", []):

            endpoint = {
                "method": ep.get("method"),
                "path": ep.get("path"),
                "summary": ep.get("summary"),
                "description": ep.get("description"),
                "security": ep.get("security", []),
            }

            # --------------------------------------------------
            # Compatible avec les deux versions du parser
            # --------------------------------------------------

            parameter_groups = ep.get("parameters", [])

            if isinstance(parameter_groups, dict):
                iterable = parameter_groups.get("all", [])
            elif isinstance(parameter_groups, list):
                iterable = parameter_groups
            else:
                iterable = []

            params = []

            for p in iterable:
                params.append({
                    "name": p.get("name"),
                    "in": p.get("in"),
                    "required": p.get("required", False),
                    "type": p.get("type"),
                })

            endpoint["parameters"] = params

            # --------------------------------------------------
            # Path Values (valeurs concrètes pour les paramètres
            # de chemin, ex: {{petId}} -> 12)
            # --------------------------------------------------

            endpoint["pathValues"] = ep.get("pathValues", {})

            # --------------------------------------------------
            # Request Body
            # --------------------------------------------------

            endpoint["hasRequestBody"] = ep.get("requestBody") is not None

            # --------------------------------------------------
            # Response Codes
            # --------------------------------------------------

            responses = ep.get("responses", {})

            if isinstance(responses, dict):
                endpoint["responseCodes"] = list(responses.keys())
            else:
                endpoint["responseCodes"] = []

            compact["endpoints"].append(endpoint)

        return compact