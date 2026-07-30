from urllib.parse import urljoin, urlparse


class TargetResolver:

    PRISM_HOST = "http://localhost:4010"

    def resolve(
        self,
        specification: dict,
        target_host: str | None = None,
        use_mock: bool = False,
    ) -> tuple[str, bool]:

        base_url = (specification.get("baseUrl") or "").strip()

        print("=" * 80)
        print("SPECIFICATION BASE URL :", base_url)
        print("TARGET HOST :", target_host)
        print("USE MOCK :", use_mock)
        print("=" * 80)

        # --------------------------------------------------
        # 1. target_host fourni
        # --------------------------------------------------

        if target_host:

            target_host = target_host.rstrip("/")

            if base_url and self.is_relative(base_url):

                return (
                    urljoin(
                        target_host + "/",
                        base_url.lstrip("/")
                    ).rstrip("/"),
                    False
                )

            return target_host, False

        # --------------------------------------------------
        # 2. Mode Mock forcé
        # --------------------------------------------------

        if use_mock:

            print("Mode MOCK -> Prism")

            return self.PRISM_HOST, True

        # --------------------------------------------------
        # 3. Aucun serveur
        # --------------------------------------------------

        if not base_url:

            print("Aucun serveur -> Prism")

            return self.PRISM_HOST, True

        # --------------------------------------------------
        # 4. URL absolue
        # --------------------------------------------------

        if self.is_absolute(base_url):

            print("Serveur OpenAPI :", base_url)

            return base_url.rstrip("/"), False

        # --------------------------------------------------
        # 5. URL relative
        # --------------------------------------------------

        print("URL relative -> Prism")

        return self.PRISM_HOST, True

    # ====================================================

    @staticmethod
    def is_absolute(url: str) -> bool:

        parsed = urlparse(url)

        return bool(parsed.scheme and parsed.netloc)

    # ====================================================

    @staticmethod
    def is_relative(url: str) -> bool:

        return not TargetResolver.is_absolute(url)