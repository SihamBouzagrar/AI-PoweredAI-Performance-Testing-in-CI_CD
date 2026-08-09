import logging
from pathlib import Path
from services.prism_service import PrismService

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError
from services.target_resolver import TargetResolver

from models.request_models import GenerateScenarioResponse, JobStatusResponse
from models.scenario_model import Scenario
from services.api_analyzer import ApiAnalyzer
from services.groq_client import GroqClient
from services.jmeter_executor import JMeterExecutor
from services.jmx_generator import JmxGenerator
from services.job_store import job_store
from services.json_cleaner import JsonCleaner
from services.openapi_parser import OpenApiParser
from services.scenario_generator import ScenarioGenerator

logger = logging.getLogger("ai-performance-testing")

router = APIRouter()

# Services are stateless / cheap to share across requests.
parser = OpenApiParser()
analyzer = ApiAnalyzer()
generator = ScenarioGenerator()
cleaner = JsonCleaner()
jmx_generator = JmxGenerator()
executor = JMeterExecutor()
resolver = TargetResolver()
prism = PrismService()


@router.get("/health")
def health():
    return {"status": "UP"}


@router.post(
    "/generateScenario",
    response_model=GenerateScenarioResponse
)
async def generate_scenario(
    background_tasks: BackgroundTasks,

    file: UploadFile = File(...),
    threads: int | None = Form(None),
    rampUp: int |None = Form(None),
    loops: int | None = Form(None),
   
):

    prism_started = False

    try:

        # ==========================================================
        # Vérification fichier
        # ==========================================================

        if not file.filename.lower().endswith(
            (".yaml", ".yml", ".json", ".zip")
        ):
            raise HTTPException(
                status_code=400,
                detail="Le fichier doit être OpenAPI (.yaml/.json/.zip)"
            )

        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Fichier vide."
            )

        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        spec_path = upload_dir / file.filename
        spec_path.write_bytes(content)

        # ==========================================================
        # Parsing
        # ==========================================================

        specification = parser.parse(spec_path)

        # ==========================================================
        # Analyse
        # ==========================================================

        analysis = analyzer.analyze(specification)

        # ==========================================================
        # IA
        # ==========================================================

        prompt = generator.build_prompt(
            specification,
            analysis
        )

        raw = GroqClient().generate(prompt)

        scenario_dict = cleaner.clean(raw)

        if threads:
            scenario_dict.setdefault(
                "configuration",
                {}
            )["threads"] = threads

        if rampUp:
            scenario_dict.setdefault(
                "configuration",
                {}
            )["rampUp"] = rampUp

        if loops:
            scenario_dict.setdefault(
                "configuration",
                {}
            )["loops"] = loops

        scenario = Scenario.model_validate(
            scenario_dict
        )

        # ==========================================================
        # Résolution URL
        # ==========================================================

        logger.info("=" * 80)
        logger.info("SPEC BASE URL : %s", specification.get("baseUrl"))
      #logger.info("TARGET HOST : %s", target_host)

        base_url, use_prism = resolver.resolve(
            specification,
           
           
            use_mock=True
        )

        logger.info("URL cible : %s", base_url)
 # ==========================================================
# Démarrage éventuel de Prism
# ==========================================================

        if use_prism:

            
            logger.info("Mode MOCK détecté")
            logger.info("Démarrage automatique de Prism...")
            
            prism.start(spec_path)

            prism_started = True

         

        # ==========================================================
        # Génération JMX
        # ==========================================================

        jmx_path = jmx_generator.generate(
            scenario=scenario,
            base_url=base_url,
            test_name=specification.get(
                "title",
                "AI Generated Test Plan"
            ),
        )

        # ==========================================================
        # Exécution JMeter
        # ==========================================================

        job_id = job_store.create(
            jmx_file=jmx_path
        )

        background_tasks.add_task(
            executor.execute,
            jmx_path,
            job_id
        )

        return GenerateScenarioResponse(
            jobId=job_id,
            status="COMPLETED",
            jmxFile=jmx_path,
        )

    except ValidationError as exc:

        raise HTTPException(
            status_code=502,
            detail=f"Scénario IA invalide : {exc}"
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception(exc)

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

   
            
@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job inconnu.")
    return job


@router.get("/download/{job_id}/log")
def download_log(job_id: str):
    """Télécharge le fichier de log JMeter pour débogage.

    Volontairement PAS bloqué sur status == FAILED : c'est justement
    dans ce cas que ce fichier est le plus utile pour comprendre pourquoi.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job inconnu.")

    log_file = Path("generated") / job_id / "jmeter.log"
    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Fichier de log introuvable.")

    return FileResponse(log_file, filename=f"{job_id}.log", media_type="text/plain")


@router.get("/download/{job_id}/stdout")
def download_stdout(job_id: str):
    """Récupère la sortie standard de la commande JMeter.

    Même logique que pour /log : accessible même si le job a échoué.
    """
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job inconnu.")

    stdout_file = Path("generated") / job_id / "stdout.log"
    if not stdout_file.exists():
        raise HTTPException(status_code=404, detail="Sortie standard introuvable.")

    return FileResponse(stdout_file, filename=f"{job_id}-stdout.log", media_type="text/plain")


@router.get("/download/{job_id}/report")
def download_report(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job inconnu.")
    if job["status"] == "FAILED":
        raise HTTPException(status_code=409, detail=f"Le job a échoué : {job.get('error') or 'erreur inconnue'}")
    if job["status"] != "COMPLETED":
        raise HTTPException(status_code=409, detail=f"Job non terminé (status={job['status']}).")

    report = Path(job["reportDir"])
    if not report.exists():
        raise HTTPException(status_code=404, detail="Rapport introuvable.")

    filename = report.name if report.suffix == ".zip" else f"{job_id}-report.zip"
    return FileResponse(report, filename=filename, media_type="application/zip")


@router.get("/download/{job_id}/jtl")
def download_jtl(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job inconnu.")
    if job["status"] == "FAILED":
        raise HTTPException(status_code=409, detail=f"Le job a échoué : {job.get('error') or 'erreur inconnue'}")

    result_file = job.get("resultFile")
    if not result_file or not Path(result_file).exists():
        raise HTTPException(status_code=404, detail="Fichier de résultats introuvable.")

    return FileResponse(result_file, filename=f"{job_id}.jtl", media_type="text/csv")