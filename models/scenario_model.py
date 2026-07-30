from pydantic import BaseModel
from typing import List, Dict, Optional, Any


class Configuration(BaseModel):
    threads: int
    rampUp: int
    loops: int
    thinkTimeMin: int
    thinkTimeMax: int


class Transaction(BaseModel):
    name: str
    method: str
    path: str
    weight: int

    headers: Optional[Dict[str, str]] = {}
    body: Optional[Dict] = None
    pathValues: Optional[Dict[str, Any]] = {}


class Assertion(BaseModel):
    path: str
    method: Optional[str] = None
    expectedStatus: int


class Scenario(BaseModel):

    configuration: Configuration

    transactions: List[Transaction]

    assertions: List[Assertion]