import asyncio
import json
import re
import subprocess
from datetime import datetime, timedelta
from resolver.resolver import Resolver
from resolver.run_results import Result, SkippedRun
from shared.shared import dump


class NetworkTracerouteResolver(Resolver):
    resolver_id = "network-traceroute"
    default_interval = 60

    def run(self, server: "Server", last_result: Result|None):
        if last_result and (datetime.now() < last_result.timestamp + timedelta(seconds=self.default_interval)):
            return SkippedRun(self, f"last mtr run < {self.default_interval}s ago")

        self.logger.debug(f"Performing traceroute to '{server.hostname}'")

        mtr_result = self._run_mtr(server.hostname)
        print(self._format_mtr_text(mtr_result["hops"]))

        return Result(
            metrics={
                "packet_count": mtr_result["count"],
                "num_hops": mtr_result["num_hops"],
                "worst_loss": mtr_result["worst_loss"],
                "worst_latency": mtr_result["worst_latency"],
            },
            timestamp=datetime.now(),
            resolver=self
        )

    def _run_mtr(self, host: str, count: int = 10):
        """
        Run MTR in JSON report mode and parse output.

        Returns:
            dict with:
                hops: list of dicts {hop, loss, sent, avg, host}
                num_hops: int
                worst_loss: float
                worst_latency: float (ms)
        """
        try:
            proc = subprocess.run(
                ["mtr", "--json", "-c", str(count), "-n", host],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        except FileNotFoundError:
            raise RuntimeError("mtr command not found. Install it first (sudo apt install mtr-tiny).")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"MTR failed: {e.stderr}")

        data = json.loads(proc.stdout)
        hops = []
        worst_loss = 0.0
        worst_latency = 0.0

        for hop_data in data.get("report", {}).get("hubs", []):
            hop = hop_data.get("count")
            loss = float(hop_data.get("LossPercent", 0))
            sent = int(hop_data.get("Snt", count))
            avg_latency = float(hop_data.get("Avg", 0))
            host_addr = hop_data.get("host", "*")

            hops.append({
                "hop": hop,
                "loss": loss,
                "sent": sent,
                "avg": avg_latency,
                "host": host_addr,
            })

            # skip 100% packet loss for worst calculation
            if loss < 100:
                worst_loss = max(worst_loss, loss)
                worst_latency = max(worst_latency, avg_latency)

        return {
            "count": count,
            "hops": hops,
            "num_hops": len(hops),
            "worst_loss": worst_loss,
            "worst_latency": worst_latency,
        }

    def _format_mtr_text(self, hops_data):
        hop_w = 3
        loss_w = 5
        sent_w = 4
        avg_w = 7
        host_w = max(len(h["host"]) for h in hops_data) if hops_data else 20

        table_lines = ["{:<{}} {:>{}} {:>{}} {:>{}} {:<{}}".format(
            "Hop", hop_w,
            "Loss%", loss_w + 1,
            "Sent", sent_w,
            "Avg", avg_w + 2,
            "Host", host_w
        )]

        for hop in hops_data:
            table_lines.append(
                "{:<{}} {:>{}.1f}% {:>{}} {:>{}.2f}ms {:<{}}".format(
                    hop["hop"], hop_w,
                    hop["loss"], loss_w,
                    hop["sent"], sent_w,
                    hop["avg"], avg_w,
                    hop["host"], host_w
                )
            )

        return "\n".join(table_lines)
