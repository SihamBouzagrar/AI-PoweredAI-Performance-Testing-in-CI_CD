import logging
import os
import shutil
import subprocess
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from services.job_store import job_store

logger = logging.getLogger("ai-performance-testing")


class JMeterExecutionError(Exception):
    """Erreur d'exécution JMeter."""
    pass


class JMeterExecutor:

    def __init__(self):
        configured = os.getenv("JMETER_EXECUTABLE", "jmeter")
        self.jmeter = self._resolve_binary(configured)
        self.timeout = int(os.getenv("JMETER_TIMEOUT", "1800"))

    # ----------------------------------------------------------

    @staticmethod
    def _resolve_binary(configured: str) -> str:

        path = Path(configured)

        if path.exists():
            logger.info("JMeter trouvé : %s", path)
            return str(path)

        found = shutil.which(configured)

        if found:
            logger.info("JMeter trouvé dans PATH : %s", found)
            return found

        candidates = [
            r"C:\jmeter\apache-jmeter-5.6.3\bin\jmeter.bat",
            r"C:\apache-jmeter-5.6.3\bin\jmeter.bat",
            r"C:\Program Files\apache-jmeter-5.6.3\bin\jmeter.bat",
            "/opt/jmeter/bin/jmeter",
        ]

        for candidate in candidates:
            if Path(candidate).exists():
                logger.info("JMeter trouvé : %s", candidate)
                return candidate

        logger.warning("JMeter introuvable.")
        return configured

    # ----------------------------------------------------------

    @staticmethod
    def _validate_jmx(jmx: Path):
        try:
            ET.parse(jmx)
        except Exception as exc:
            raise JMeterExecutionError(
                f"Fichier JMX invalide : {exc}"
            )

    # ----------------------------------------------------------

    @staticmethod
    def _build_command(
        jmeter_bin: Path,
        jmx: Path,
        result: Path,
        report: Path,
        log: Path,
    ):
        return [
            str(jmeter_bin),
            "-n",
            "-t", str(jmx),
            "-l", str(result),
            "-e",
            "-o", str(report),
            "-j", str(log),
            "-f",
        ]

    # ----------------------------------------------------------

    @staticmethod
    def _zip_report(report_dir: Path):

        if not report_dir.exists():
            return None

        archive = report_dir.with_suffix(".zip")

        with zipfile.ZipFile(
            archive,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as zipf:

            for file in report_dir.rglob("*"):
                zipf.write(
                    file,
                    file.relative_to(report_dir.parent),
                )

        return archive

    # ----------------------------------------------------------

    def execute(self, jmx_file: str, job_id: str):

        logger.info("===================================")
        logger.info("Début exécution JMeter")
        logger.info("Job : %s", job_id)

        jmeter_bin = Path(self.jmeter)
        jmx = Path(jmx_file).resolve()

        # -----------------------
        # Vérifications
        # -----------------------

        if not jmeter_bin.exists():
            error = f"JMeter introuvable : {jmeter_bin}"
            logger.error(error)
            job_store.update(
                job_id,
                status="FAILED",
                finishedAt=time.time(),
                error=error,
            )
            return

        if not jmx.exists():
            error = f"JMX introuvable : {jmx}"
            logger.error(error)
            job_store.update(
                job_id,
                status="FAILED",
                finishedAt=time.time(),
                error=error,
            )
            return

        try:
            self._validate_jmx(jmx)
        except Exception as e:
            job_store.update(
                job_id,
                status="FAILED",
                finishedAt=time.time(),
                error=str(e),
            )
            return

        # -----------------------
        # Répertoire de sortie
        # -----------------------

        output = (Path("generated") / job_id).resolve()
        output.mkdir(parents=True, exist_ok=True)

        result = (output / "results.jtl").resolve()
        report = (output / "report").resolve()
        log = (output / "jmeter.log").resolve()
        stdout = (output / "stdout.log").resolve()

        command = self._build_command(
            jmeter_bin,
            jmx,
            result,
            report,
            log,
        )

        logger.info("Commande : %s", " ".join(command))

        job_store.update(
            job_id,
            status="RUNNING",
            startedAt=time.time(),
        )

        # -----------------------
        # Exécution
        # -----------------------

        try:
            logger.info("========================================")
            logger.info("Lancement de JMeter")
            logger.info("Working directory : %s", Path.cwd())
            logger.info("Executable : %s", jmeter_bin)
            logger.info("JMX : %s", jmx)
            logger.info("Commande : %s", " ".join(command))

            process = subprocess.run(
                command,
                cwd=Path.cwd(),
                capture_output=True,
                text=True,
                timeout=self.timeout,
                stdin=subprocess.DEVNULL,
            )

        except subprocess.TimeoutExpired:
            job_store.update(
                job_id,
                status="FAILED",
                finishedAt=time.time(),
                error="Timeout",
            )
            return

        except Exception as e:
            job_store.update(
                job_id,
                status="FAILED",
                finishedAt=time.time(),
                error=str(e),
            )
            return

        stdout.write_text(
            (process.stdout or "")
            + "\n\nSTDERR\n"
            + (process.stderr or ""),
            encoding="utf-8",
        )

        logger.info("Return Code : %s", process.returncode)

        # -----------------------
        # Vérification des fichiers
        # -----------------------

        result_exists = result.exists()
        report_exists = report.exists() and any(report.iterdir())
        log_exists = log.exists()

        logger.info("results.jtl : %s", result_exists)
        logger.info("report : %s", report_exists)
        logger.info("log : %s", log_exists)

        if process.returncode != 0:
            job_store.update(
                job_id,
                status="FAILED",
                finishedAt=time.time(),
                returnCode=process.returncode,
                error=process.stderr or process.stdout,
            )
            return

        if not result_exists:
            job_store.update(
                job_id,
                status="FAILED",
                finishedAt=time.time(),
                error="results.jtl non généré.",
            )
            return

        report_zip = None
        if report_exists:
            report_zip = self._zip_report(report)

        job_store.update(
            job_id,
            status="COMPLETED",
            finishedAt=time.time(),
            returnCode=0,
            resultFile=str(result),
            reportDir=str(report_zip if report_zip else report),
            logFile=str(log),
            stdoutFile=str(stdout),
        )

        logger.info("Exécution terminée.")
        logger.info("===================================")