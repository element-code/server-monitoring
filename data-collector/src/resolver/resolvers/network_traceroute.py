import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone

import idna

from resolver.resolver import Resolver
from resolver.run_results import Result, SkippedRun
from shared.shared import now

BASE_STORAGE_PATH = "/storage/traceroutes"
DOMAIN_RE = re.compile(r"^[a-z0-9.-]+$")


class NetworkTracerouteResolver(Resolver):
    resolver_id = "network-traceroute"
    default_interval = 60

    def run(self, server: "Server", last_result: Result | None):
        timestamp = now()
        if last_result and (timestamp < last_result.timestamp + timedelta(seconds=self.default_interval)):
            return SkippedRun(self, f"last mtr run < {self.default_interval}s ago")

        self.logger.debug(f"Performing traceroute to '{server.hostname}'")

        mtr_result = self._run_mtr(server.hostname)
        mtr_text = self._format_mtr_text(mtr_result["hops"])
        file_path = self._store_mtr_output(server.hostname, mtr_text, timestamp)
        self.logger.debug(f"Stored traceroute at '{file_path}'")

        return Result(
            metrics={
                "packet_count": mtr_result["count"],
                "num_hops": mtr_result["num_hops"],
                "worst_loss": mtr_result["worst_loss"],
                "worst_latency": mtr_result["worst_latency"],
            },
            timestamp=timestamp,
            resolver=self
        )

    def _run_mtr(self, host: str, count: int = 10):
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

    def _normalize_server_id(self, hostname: str) -> str:
        hostname = hostname.strip().lower()

        if hostname.endswith("."):
            hostname = hostname[:-1]

        try:
            hostname = idna.encode(hostname).decode("ascii")
        except idna.IDNAError as e:
            raise ValueError(f"Invalid IDN hostname: {hostname}") from e

        if not DOMAIN_RE.match(hostname):
            raise ValueError(f"Unsafe hostname for filesystem use: {hostname}")

        return hostname.replace(":", "-")

    def _store_mtr_output(self, server_id: str, text: str, timestamp: datetime) -> str:
        timestamp_utc = timestamp.astimezone(timezone.utc)
        dir_path = os.path.join(BASE_STORAGE_PATH, self._normalize_server_id(server_id))
        file_path = os.path.join(dir_path, f"{timestamp_utc.strftime("%Y-%m-%dT%H-%M-%SZ")}.txt")

        os.makedirs(dir_path, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write('Collected at: ' + timestamp.isoformat() + '\n' + text)

        return file_path
