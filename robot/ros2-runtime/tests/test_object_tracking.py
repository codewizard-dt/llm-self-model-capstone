from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vexy_ros.object_tracking import ObjectIndication, ObjectTracker


class ObjectTrackingTests(unittest.TestCase):
    def test_promotes_track_after_repeated_hits_and_keeps_stable_id(self) -> None:
        tracker = ObjectTracker(min_hits=2, association_gate_m=0.25)

        first = tracker.update([_indication(0.70, -0.05)], now_s=10.0)[0]
        second = tracker.update([_indication(0.72, -0.04)], now_s=10.2)[0]

        self.assertEqual(first.track_id, second.track_id)
        self.assertEqual(
            first.status(
                now_s=10.0, min_hits=2, stale_after_s=0.75, expire_after_s=3.0
            ),
            "candidate",
        )
        self.assertEqual(
            second.status(
                now_s=10.2, min_hits=2, stale_after_s=0.75, expire_after_s=3.0
            ),
            "confirmed",
        )
        self.assertEqual(second.seen_frames, 2)

    def test_marks_confirmed_track_stale_then_expired_without_deleting_immediately(
        self,
    ) -> None:
        tracker = ObjectTracker(min_hits=1, stale_after_s=0.5, expire_after_s=1.0)
        tracker.update([_indication(0.70, -0.05)], now_s=10.0)

        stale = tracker.payload(now_s=10.7, include_expired=True)["tracks"][0]
        expired = tracker.payload(now_s=11.2, include_expired=True)["tracks"][0]

        self.assertEqual(stale["status"], "stale")
        self.assertEqual(expired["status"], "expired")

    def test_class_mismatch_creates_distinct_track(self) -> None:
        tracker = ObjectTracker(min_hits=1, association_gate_m=1.0)

        tracker.update([_indication(0.70, -0.05, name="yellow_ball")], now_s=10.0)
        tracks = tracker.update([_indication(0.72, -0.05, name="bin")], now_s=10.1)

        self.assertEqual([track.class_name for track in tracks], ["bin", "yellow_ball"])


def _indication(
    forward_m: float,
    left_m: float,
    *,
    name: str = "yellow_ball",
) -> ObjectIndication:
    return ObjectIndication(
        name=name,
        forward_m=forward_m,
        left_m=left_m,
        stamp_s=10.0,
        confidence=0.8,
        source="yellow_hsv",
        range_source="bbox_size",
        position_uncertainty_m=0.12,
    )


if __name__ == "__main__":
    unittest.main()
