from dataclasses import dataclass
from datetime import datetime
from typing import Dict
from resolver.resolver import Resolver

class BaseResult:
    timestamp: datetime
    resolver: "Resolver"

    def __init__(self, resolver: "Resolver"):
        self.timestamp = datetime.now()
        self.resolver = resolver

    pass


class Result(BaseResult):
    metrics: Dict[str, float]
    timestamp: datetime

    def __init__(self, resolver: "Resolver", metrics: Dict[str, float], timestamp: datetime):
        super().__init__(resolver)
        self.metrics = metrics
        self.timestamp = timestamp


class SkippedRun(BaseResult):
    timestamp: datetime

    def __init__(self, resolver: "Resolver", reason: str):
        super().__init__(resolver)
        self.reason = reason
