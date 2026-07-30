from typing import Optional
from pydantic import BaseModel


class ConfigOverride(BaseModel):
    """Optional overrides sent alongside the OpenAPI file to force
    specific load-test parameters instead of letting the AI decide."""

    threads: Optional[int] = None
    rampUp: Optional[int] = None
    loops: Optional[int] = None


class GenerateScenarioResponse(BaseModel):
    jobId: str
    status: str
    jmxFile: str


class JobStatusResponse(BaseModel):
    jobId: str
    status: str
    createdAt: float
    startedAt: Optional[float] = None
    finishedAt: Optional[float] = None
    jmxFile: Optional[str] = None
    resultFile: Optional[str] = None
    reportDir: Optional[str] = None
    returnCode: Optional[int] = None
    error: Optional[str] = None
