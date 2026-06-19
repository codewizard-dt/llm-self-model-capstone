from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from . import protocol
from .state import atomic_write_json, ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-owner Raspberry Pi camera broker")
    parser.add_argument("--state-dir", default=os.getenv("VEXY_STATE_DIR", "/tmp/vexy-system2"))
    parser.add_argument("--width", type=int, default=int(os.getenv("VEXY_CAMERA_WIDTH", "640")))
    parser.add_argument("--height", type=int, default=int(os.getenv("VEXY_CAMERA_HEIGHT", "480")))
    parser.add_argument("--fps", type=float, default=float(os.getenv("VEXY_CAMERA_FPS", "5")))
    return parser.parse_args()


def write_synthetic(path: Path, width: int, height: int, message: str) -> None:
    try:
        import cv2
        import numpy as np

        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (28, 34, 38)
        cv2.putText(frame, "Vexy camera broker", (24, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (220, 240, 255), 2)
        cv2.putText(frame, message[:64], (24, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (90, 220, 180), 1)
        cv2.imwrite(str(path), frame)
    except Exception:
        path.write_bytes(b"")


def main() -> None:
    args = parse_args()
    state_dir = ensure_dir(args.state_dir)
    latest = state_dir / "latest.jpg"
    interval = 1.0 / max(args.fps, 0.1)

    try:
        import cv2
        from picamera2 import Picamera2

        cam = Picamera2()
        cam.configure(cam.create_video_configuration(main={"size": (args.width, args.height), "format": "RGB888"}))
        cam.start()
        mode = "camera"
        error = None
    except Exception as exc:
        cam = None
        cv2 = None
        mode = "synthetic"
        error = str(exc)

    print(f"camera broker mode={mode}", flush=True)
    try:
        while True:
            updated = protocol.now_ms()
            if cam is not None:
                frame = cam.capture_array()
                bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(str(latest), bgr)
            else:
                write_synthetic(latest, args.width, args.height, error or "camera unavailable")

            atomic_write_json(
                state_dir / "camera.json",
                {
                    "updated_ms": updated,
                    "mode": mode,
                    "width": args.width,
                    "height": args.height,
                    "fps_target": args.fps,
                    "latest_jpg": str(latest),
                    "error": error,
                },
            )
            time.sleep(interval)
    finally:
        if cam is not None:
            cam.stop()


if __name__ == "__main__":
    main()

