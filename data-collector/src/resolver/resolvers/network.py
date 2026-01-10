from datetime import datetime
from ping3 import ping
import statistics
from resolver.resolver import Resolver
from resolver.run_results import Result


class NetworkResolver(Resolver):
    resolver_id = "network"

    def run(self, server: "Server", last_result: Result|None):
        times = []
        packets = 10
        for _ in range(packets):
            rtt = ping(server.hostname, timeout=10)
            if rtt is not None and rtt is not False:
                times.append(rtt * 1000)

        if times:
            avg = statistics.mean(times)
            min_rtt = min(times)
            max_rtt = max(times)
            packet_loss = 100 * (1 - len(times) / packets)
        else:
            self.logger.warning(f"ping failed for '{server.hostname}'")
            avg = min_rtt = max_rtt = 0
            packet_loss = 100

        return Result(
            metrics={
                "packet_count": len(times),
                "ping_min": min_rtt,
                "ping_max": max_rtt,
                "ping_avg": avg,
                "packet_loss": packet_loss,
            },
            timestamp=datetime.now(),
            resolver=self
        )
