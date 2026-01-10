import time

from resolver.run_results import Result, SkippedRun
from shared.cache import ResultCache
from shared.config import Config
from shared.shared import logger

logger = logger('collector')


class DataCollector:
    def __init__(self, config: Config, cache: ResultCache):
        self.cache = cache
        self.config = config

    def run(self):
        while True:
            for server in self.config.servers:
                logger.debug(f'resolving data for server "{server.hostname}"')
                for resolver in server.resolvers:
                    try:
                        result = resolver.run(server, self.cache.get(server.hostname, resolver.resolver_id))

                        if isinstance(result, Result):
                            self.cache.update(server.hostname, resolver.resolver_id, result)
                        elif isinstance(result, SkippedRun):
                            logger.debug(f"Skipped {resolver.resolver_id} run for {server.hostname}: {result.reason}")
                        else:
                            raise ValueError("resolver response has to be of type Result|SkippedRun")
                    except BaseException as exception:
                        resolver.logger.exception(exception)

            time.sleep(self.config.run_interval)


def invoke(config: Config, cache: ResultCache):
    try:
        DataCollector(config, cache).run()
    except BaseException as exception:
        logger.exception(exception)
