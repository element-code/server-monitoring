import importlib
import pathlib
from abc import ABC, abstractmethod
from logging import Logger
from typing import Dict, Type, Union
import shared.shared


class Resolver(ABC):
    _registry: Dict[str, Type["Resolver"]] = {}

    resolver_id: str

    def __init__(self, config: dict, logger: Logger):
        self.config = config
        self.logger = logger

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "resolver_id") or not cls.resolver_id:
            raise TypeError(f"{cls.__name__} must define a class-level 'resolver_id'")

        Resolver._registry[cls.resolver_id] = cls

    @classmethod
    def create(cls, resolver_id: str, *args, **kwargs) -> "Resolver":
        resolver_cls = cls._registry.get(resolver_id)
        if resolver_cls is None:
            raise ValueError(f"Resolver '{resolver_id}' is not registered")
        return resolver_cls(logger=shared.shared.logger(f"collector.resolver.{resolver_id}"), *args, **kwargs)

    @abstractmethod
    def run(self, server: "Server", last_result: Union["Result", None]) -> "BaseResult":
        pass


modules_path = pathlib.Path(__file__).parent / "resolvers"

for py_file in modules_path.glob("*.py"):
    if py_file.stem == "__init__":
        continue
    importlib.import_module(f"resolver.resolvers.{py_file.stem}")
