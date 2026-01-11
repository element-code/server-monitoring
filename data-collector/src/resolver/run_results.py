from datetime import datetime
from typing import Dict

from resolver.resolver import Resolver
from shared.shared import now


class BaseResult:
    timestamp: datetime
    resolver: "Resolver"

    def __init__(self, resolver: "Resolver"):
        self.timestamp = now()
        self.resolver = resolver

    pass


class Result(BaseResult):
    metrics: Dict[str, float]

    def __init__(self, resolver: "Resolver", metrics: Dict[str, float], timestamp: datetime | None = None):
        super().__init__(resolver)
        self.metrics = metrics
        if timestamp is not None:
            self.timestamp = timestamp


class SkippedRun(BaseResult):
    def __init__(self, resolver: "Resolver", reason: str):
        super().__init__(resolver)
        self.reason = reason
