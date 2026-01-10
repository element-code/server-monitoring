import os
import yaml
from resolver.resolver import Resolver
from shared.shared import Printable


class Server(Printable):
    def __init__(self, hostname: str, resolvers: list[Resolver]):
        self.hostname: str = hostname
        self.resolvers: list[Resolver] = resolvers


class ConfigDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __getitem__(self, key):
        return super().__getitem__(key)

class Config:
    def __init__(self, path: str):
        with open(path) as f:
            self.raw = yaml.safe_load(f)
            self.raw = self._expand_env(self.raw)
            self.config = self._to_object(self.raw)
            self._servers: list[Server] = []

    def _expand_env(self, obj):
        if isinstance(obj, dict):
            return {k: self._expand_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env(v) for v in obj]
        elif isinstance(obj, str):
            return os.path.expandvars(obj)
        else:
            return obj

    def _to_object(self, obj):
        if isinstance(obj, dict):
            return ConfigDict({k: self._to_object(v) for k, v in obj.items()})
        elif isinstance(obj, list):
            return [self._to_object(x) for x in obj]
        else:
            return obj

    @property
    def servers(self) -> list[Server]:
        if not self._servers:
            for s in self.config.servers:
                resolvers = [Resolver.create('network', {}), Resolver.create('network-traceroute', {})]
                for rid, rconf in s.get("resolvers", {}).items():
                    resolver = Resolver.create(rid, rconf)
                    resolvers.append(resolver)
                server = Server(s.hostname, resolvers)
                self._servers.append(server)
        return self._servers

    @property
    def run_interval(self) -> int:
        return self.raw["global"]["run_interval_seconds"]
