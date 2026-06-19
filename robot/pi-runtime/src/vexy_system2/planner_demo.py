from __future__ import annotations

import argparse
import os
import time

from . import protocol
from .client import send_packet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Small simulated System 2 planner")
    parser.add_argument("--goal", default="stay safe")
    parser.add_argument("--host", default=os.getenv("VEXY_BRIDGE_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("VEXY_BRIDGE_PORT", "8765")))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seq = 1
    print(f"goal: {args.goal}")
    for _ in range(2):
        print(send_packet(protocol.heartbeat(seq), args.host, args.port))
        seq += 1
        time.sleep(0.05)

    cautious_nudge = protocol.command(seq, "drive", vx=0.10, vy=0.0, omega=0.0, ttl_ms=150)
    print(send_packet(cautious_nudge, args.host, args.port))
    seq += 1
    time.sleep(0.1)

    print(send_packet(protocol.stop(seq, reason="planner_demo_complete"), args.host, args.port))


if __name__ == "__main__":
    main()

