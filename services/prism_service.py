import shutil
import subprocess
import time
from pathlib import Path

import requests


class PrismService:

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 4010

    def __init__(self):
        self.process = None

    @property
    def base_url(self):
        return f"http://{self.DEFAULT_HOST}:{self.DEFAULT_PORT}"

    # -----------------------------------------------------

    def is_running(self) -> bool:
        """
        Prism répond dès que le port HTTP est ouvert.
        Peu importe que la réponse soit 200, 401 ou 404.
        """

        try:
            requests.get(self.base_url, timeout=1)
            return True

        except requests.ConnectionError:
            return False

        except requests.RequestException:
            # serveur HTTP présent
            return True

    # -----------------------------------------------------

    def start(self, openapi_file: str | Path):

        if self.is_running():
            print("Prism déjà démarré.")
            return

        prism = shutil.which("prism")

        if prism is None:
            raise RuntimeError(
                "Prism CLI introuvable.\n"
                "Installer avec : npm install -g @stoplight/prism-cli"
            )

        openapi_file = str(Path(openapi_file).resolve())

        command = [
            prism,
            "mock",
            openapi_file,
            "--host",
            self.DEFAULT_HOST,
            "--port",
            str(self.DEFAULT_PORT),
        ]

        print("=" * 80)
        print("Lancement Prism")
        print(command)
        print("=" * 80)

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # attendre max 20 s
        for _ in range(40):

            # Prism a crashé
            if self.process.poll() is not None:
                raise RuntimeError("Prism s'est arrêté immédiatement.")

            if self.is_running():
                print("Prism démarré.")
                return

            time.sleep(0.5)

        raise RuntimeError("Prism ne répond pas.")

    # -----------------------------------------------------

    def stop(self):

        if self.process is None:
            return

        if self.process.poll() is None:
            self.process.terminate()

            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        self.process = None

        print("Prism arrêté.")