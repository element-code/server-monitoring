from datetime import datetime
import requests

from resolver.resolver import Resolver
from resolver.run_results import Result
from shared.cache import LabeledMetric


class HLLCrconResolver(Resolver):
    resolver_id = "hll-crcon"

    def run(self, server: "Server", last_result: Result|None):
        state_result = self._query_rcon("get_gamestate")
        status_result = self._query_rcon("get_status")

        return Result(
            metrics={
                "player_count": status_result['result']['current_players'],
                "game_time": state_result['result']['match_time'] - state_result['result']['time_remaining'],
                "current_map": LabeledMetric(1, state_result['result']['current_map']['map']['id']),
                "game_mode": LabeledMetric(1, state_result['result']['current_map']['game_mode']),
            },
            timestamp=datetime.now(),
            resolver=self
        )

    def _query_rcon(self, endpoint: str) -> dict:
        response = requests.get(f"{self.config.base_url}/{endpoint}", headers={
            "Authorization": f"Bearer {self.config.api_key}"
        }, timeout=5)
        response.raise_for_status()

        result = response.json()
        if result['failed']:
            raise RuntimeError(result['error'])

        return result
