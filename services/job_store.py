import threading
import time
import uuid
from typing import Optional


class JobStore:
    """
    Thread-safe in-memory store.

    Suit à l'état des exécutions JMeter.

    États :
        QUEUED
        RUNNING
        COMPLETED
        FAILED
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}

    # ---------------------------------------------------------

    def create(self, jmx_file: str) -> str:

        job_id = uuid.uuid4().hex

        with self._lock:

            self._jobs[job_id] = {

                "jobId": job_id,

                "status": "QUEUED",

                "createdAt": time.time(),

                "startedAt": None,

                "finishedAt": None,

                "jmxFile": jmx_file,

                "resultFile": None,

                "reportDir": None,

                "logFile": None,

                "stdoutFile": None,

                "returnCode": None,

                "error": None,

            }

        return job_id

    # ---------------------------------------------------------

    def update(self, job_id: str, **fields):

        with self._lock:

            job = self._jobs.get(job_id)

            if job is None:
                return False

            job.update(fields)

            return True

    # ---------------------------------------------------------

    def get(self, job_id: str) -> Optional[dict]:

        with self._lock:

            job = self._jobs.get(job_id)

            if job is None:
                return None

            return job.copy()

    # ---------------------------------------------------------

    def exists(self, job_id: str) -> bool:

        with self._lock:

            return job_id in self._jobs

    # ---------------------------------------------------------

    def delete(self, job_id: str):

        with self._lock:

            self._jobs.pop(job_id, None)

    # ---------------------------------------------------------

    def list(self):

        with self._lock:

            return [job.copy() for job in self._jobs.values()]


job_store = JobStore()