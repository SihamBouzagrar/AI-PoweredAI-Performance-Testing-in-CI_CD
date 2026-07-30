from pathlib import Path
import shutil
import tempfile
import zipfile


class FileService:

    OPENAPI_NAMES = {
        "openapi.yaml",
        "openapi.yml",
        "swagger.yaml",
        "swagger.yml",
        "openapi.json",
        "swagger.json",
    }

    # =========================================================

    def extract_zip(self, zip_path: Path) -> Path:
        """
        Décompresse un projet OpenAPI complet.

        Retourne le dossier temporaire contenant
        l'intégralité du projet.
        """

        if not zip_path.exists():
            raise FileNotFoundError(zip_path)

        workspace = Path(
            tempfile.mkdtemp(prefix="openapi_")
        )

        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(workspace)

        return workspace

    # =========================================================

    def find_openapi_file(
        self,
        root: Path
    ) -> Path:
        """
        Recherche automatiquement le fichier
        OpenAPI principal dans tout le projet.
        """

        root = Path(root)

        if root.is_file():
            return root

        for file in root.rglob("*"):

            if not file.is_file():
                continue

            if file.name.lower() in self.OPENAPI_NAMES:
                return file

        raise FileNotFoundError(
            "Aucun fichier OpenAPI trouvé."
        )

    # =========================================================

    def prepare(self, path: Path) -> Path:
        """
        Accepte :

        - YAML
        - JSON
        - ZIP

        Retourne directement le fichier OpenAPI
        principal.
        """

        path = Path(path)

        suffix = path.suffix.lower()

        if suffix in {".yaml", ".yml", ".json"}:
            return path

        if suffix == ".zip":

            workspace = self.extract_zip(path)

            return self.find_openapi_file(workspace)

        raise ValueError(
            "Format non supporté."
        )

    # =========================================================

    def cleanup(
        self,
        workspace: Path
    ) -> None:

        workspace = Path(workspace)

        if workspace.exists():
            shutil.rmtree(
                workspace,
                ignore_errors=True
            )