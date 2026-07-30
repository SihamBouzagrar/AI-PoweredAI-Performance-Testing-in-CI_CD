class ApiAnalyzer:

    def analyze(self, specification):

        endpoints = specification.get("endpoints", [])

        analysis = {
            "totalEndpoints": len(endpoints),
            "get": 0,
            "post": 0,
            "put": 0,
            "delete": 0,
            "patch": 0,
            "authentication": False,
            "bankingOperations": 0
        }

        keywords = [
            "auth",
            "login",
            "token",
            "transfer",
            "payment",
            "transaction",
            "account",
            "beneficiary"
        ]

        for endpoint in endpoints:

            method = endpoint["method"].upper()

            if method == "GET":
                analysis["get"] += 1

            elif method == "POST":
                analysis["post"] += 1

            elif method == "PUT":
                analysis["put"] += 1

            elif method == "DELETE":
                analysis["delete"] += 1

            elif method == "PATCH":
                analysis["patch"] += 1

            path = endpoint["path"].lower()

            if any(k in path for k in ["auth", "login", "token"]):
                analysis["authentication"] = True

            if any(k in path for k in keywords):
                analysis["bankingOperations"] += 1

        return analysis