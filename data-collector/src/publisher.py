from datetime import timezone

from aiohttp import web
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

from shared.cache import ResultCache, LabeledMetric
from shared.config import Config
from shared.shared import logger

logger = logger('publisher')


class Publisher:
    def __init__(self, config: Config, cache: ResultCache):
        self.cache = cache
        self.config = config
        self.host = '0.0.0.0'
        self.port = 80
        self.gauges = {}
        self.app = web.Application()
        self.app.add_routes([web.get("/metrics", self._metrics)])

    def _get_gauge(self, name: str, label_names: tuple[str, ...]):
        key = (name, label_names)
        if key not in self.gauges:
            self.gauges[key] = Gauge(
                name,
                name,
                ["server_id", *label_names],
            )
        return self.gauges[key]

    def _set_metric(self, server_id: str, metric_name: str, value):
        if isinstance(value, LabeledMetric):
            label_name = f"{metric_name}_label"

            gauge = self._get_gauge(
                metric_name,
                (label_name,)
            )

            gauge.labels(
                server_id=server_id,
                **{label_name: value.label}
            ).set(value.value)

        else:
            gauge = self._get_gauge(metric_name, ())
            gauge.labels(
                server_id=server_id
            ).set(float(value))

    async def _metrics(self, request):
        for server_id, resolvers in self.cache.get_all().items():
            for resolver_id, result in resolvers.items():
                self._set_metric(
                    server_id,
                    f"{resolver_id}_timestamp",
                    result.timestamp.astimezone(timezone.utc).timestamp()
                )

                for metric, value in result.metrics.items():
                    self._set_metric(server_id, f"{resolver_id}_{metric}", value)

        return web.Response(
            body=generate_latest(),
            headers={"Content-Type": CONTENT_TYPE_LATEST},
        )

    def run(self):
        logger.info(f"Starting metrics endpoint on http://{self.host}:{self.port}/metrics")
        web.run_app(self.app, host=self.host, port=self.port)


def invoke(config: Config, cache: ResultCache):
    try:
        Publisher(config, cache).run()
    except BaseException as exception:
        logger.exception(exception)
