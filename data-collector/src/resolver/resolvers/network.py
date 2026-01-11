import statistics

from ping3 import ping

from resolver.resolver import Resolver
from resolver.run_results import Result


class NetworkResolver(Resolver):
    resolver_id = "network"

    def run(self, server: "Server", last_result: Result | None):
        times = []
        packets = 10

        for _ in range(packets):
            rtt = ping(server.hostname, timeout=10)
            if rtt is not None and rtt is not False:
                times.append(rtt * 1000)

        if times:
            ping_min = min(times)
            ping_max = max(times)
            ping_avg = statistics.mean(times)

            jitter = statistics.pstdev(times) if len(times) > 1 else 0.0

            packet_loss = 100 * (1 - len(times) / packets)

        else:
            self.logger.warning(f"ping failed for '{server.hostname}'")
            ping_min = ping_max = ping_avg = jitter = 0.0
            packet_loss = 100.0

        return Result(
            metrics={
                "packet_count": len(times),
                "ping_min": ping_min,
                "ping_max": ping_max,
                "ping_avg": ping_avg,
                "jitter": jitter,
                "packet_loss": packet_loss,
            },
            resolver=self,
        )
