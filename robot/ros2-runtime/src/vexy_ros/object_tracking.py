from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from typing import Any, Mapping


@dataclass(frozen=True)
class ObjectIndication:
    name: str
    forward_m: float
    left_m: float
    stamp_s: float
    confidence: float
    source: str = "object_detector"
    range_source: str = "bbox_size"
    position_uncertainty_m: float | None = None
    bbox_xyxy: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class ObjectTrack:
    track_id: str
    class_name: str
    forward_m: float
    left_m: float
    first_seen_s: float
    last_seen_s: float
    seen_frames: int
    missed_frames: int
    confidence: float
    source: str
    range_source: str
    position_uncertainty_m: float
    bbox_xyxy: tuple[float, float, float, float] | None = None

    def status(
        self,
        *,
        now_s: float,
        min_hits: int,
        stale_after_s: float,
        expire_after_s: float,
    ) -> str:
        age_s = max(0.0, now_s - self.last_seen_s)
        if age_s >= expire_after_s:
            return "expired"
        if self.seen_frames < min_hits:
            return "candidate"
        if age_s >= stale_after_s:
            return "stale"
        return "confirmed"

    def to_json(
        self,
        *,
        now_s: float,
        min_hits: int,
        stale_after_s: float,
        expire_after_s: float,
    ) -> dict[str, Any]:
        status = self.status(
            now_s=now_s,
            min_hits=min_hits,
            stale_after_s=stale_after_s,
            expire_after_s=expire_after_s,
        )
        payload: dict[str, Any] = {
            "id": self.track_id,
            "class": self.class_name,
            "name": self.class_name,
            "status": status,
            "camera_pose": {
                "forward_m": self.forward_m,
                "left_m": self.left_m,
                "yaw_rad": math.atan2(self.left_m, self.forward_m),
            },
            "confidence": self.confidence,
            "first_seen_s": self.first_seen_s,
            "last_seen_s": self.last_seen_s,
            "seen_frames": self.seen_frames,
            "missed_frames": self.missed_frames,
            "source": self.source,
            "range_source": self.range_source,
            "position_uncertainty_m": self.position_uncertainty_m,
            "age_s": max(0.0, now_s - self.last_seen_s),
        }
        if self.bbox_xyxy is not None:
            payload["bbox_xyxy"] = list(self.bbox_xyxy)
        return payload


class ObjectTracker:
    def __init__(
        self,
        *,
        min_hits: int = 3,
        association_gate_m: float = 0.25,
        stale_after_s: float = 0.75,
        expire_after_s: float = 3.0,
    ) -> None:
        self.min_hits = max(1, int(min_hits))
        self.association_gate_m = float(association_gate_m)
        self.stale_after_s = float(stale_after_s)
        self.expire_after_s = float(expire_after_s)
        self._tracks: list[ObjectTrack] = []
        self._next_by_class: dict[str, int] = {}

    def update(
        self, indications: list[ObjectIndication], *, now_s: float
    ) -> list[ObjectTrack]:
        unmatched_track_indexes = set(range(len(self._tracks)))
        updated = list(self._tracks)

        for indication in indications:
            match_index = self._nearest_track_index(
                indication, unmatched_track_indexes, now_s=now_s
            )
            if match_index is None:
                updated.append(self._new_track(indication, now_s=now_s))
                continue

            track = updated[match_index]
            unmatched_track_indexes.discard(match_index)
            updated[match_index] = replace(
                track,
                forward_m=_smooth(track.forward_m, indication.forward_m, 0.45),
                left_m=_smooth(track.left_m, indication.left_m, 0.45),
                last_seen_s=now_s,
                seen_frames=track.seen_frames + 1,
                missed_frames=0,
                confidence=max(track.confidence * 0.8, indication.confidence),
                source=indication.source,
                range_source=indication.range_source,
                position_uncertainty_m=_track_uncertainty(indication),
                bbox_xyxy=indication.bbox_xyxy,
            )

        for index in unmatched_track_indexes:
            track = updated[index]
            updated[index] = replace(track, missed_frames=track.missed_frames + 1)

        self._tracks = [
            track
            for track in updated
            if now_s - track.last_seen_s <= self.expire_after_s + 2.0
        ]
        return self.tracks(now_s=now_s, include_expired=True)

    def tracks(
        self, *, now_s: float, include_expired: bool = False
    ) -> list[ObjectTrack]:
        tracks = sorted(self._tracks, key=lambda item: item.track_id)
        if include_expired:
            return tracks
        return [
            track
            for track in tracks
            if track.status(
                now_s=now_s,
                min_hits=self.min_hits,
                stale_after_s=self.stale_after_s,
                expire_after_s=self.expire_after_s,
            )
            != "expired"
        ]

    def payload(self, *, now_s: float, include_expired: bool = False) -> dict[str, Any]:
        tracks = [
            track.to_json(
                now_s=now_s,
                min_hits=self.min_hits,
                stale_after_s=self.stale_after_s,
                expire_after_s=self.expire_after_s,
            )
            for track in self.tracks(now_s=now_s, include_expired=include_expired)
        ]
        return {
            "type": "object_tracks",
            "stamp_s": now_s,
            "tracks": tracks,
            "confirmed_count": sum(
                1 for item in tracks if item["status"] == "confirmed"
            ),
            "candidate_count": sum(
                1 for item in tracks if item["status"] == "candidate"
            ),
            "stale_count": sum(1 for item in tracks if item["status"] == "stale"),
            "expired_count": sum(1 for item in tracks if item["status"] == "expired"),
        }

    def _nearest_track_index(
        self,
        indication: ObjectIndication,
        candidates: set[int],
        *,
        now_s: float,
    ) -> int | None:
        best: tuple[float, int] | None = None
        for index in candidates:
            track = self._tracks[index]
            if track.class_name != indication.name:
                continue
            if (
                track.status(
                    now_s=now_s,
                    min_hits=self.min_hits,
                    stale_after_s=self.stale_after_s,
                    expire_after_s=self.expire_after_s,
                )
                == "expired"
            ):
                continue
            distance = math.hypot(
                track.forward_m - indication.forward_m,
                track.left_m - indication.left_m,
            )
            if distance <= self.association_gate_m and (
                best is None or distance < best[0]
            ):
                best = (distance, index)
        return None if best is None else best[1]

    def _new_track(self, indication: ObjectIndication, *, now_s: float) -> ObjectTrack:
        sequence = self._next_by_class.get(indication.name, 0) + 1
        self._next_by_class[indication.name] = sequence
        return ObjectTrack(
            track_id=f"{indication.name}_{sequence:02d}",
            class_name=indication.name,
            forward_m=indication.forward_m,
            left_m=indication.left_m,
            first_seen_s=now_s,
            last_seen_s=now_s,
            seen_frames=1,
            missed_frames=0,
            confidence=indication.confidence,
            source=indication.source,
            range_source=indication.range_source,
            position_uncertainty_m=_track_uncertainty(indication),
            bbox_xyxy=indication.bbox_xyxy,
        )


def parse_object_indications(
    raw: str | Mapping[str, Any] | list[Mapping[str, Any]], *, stamp_s: float
) -> list[ObjectIndication]:
    payload: Any = json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(payload, Mapping):
        payload = payload.get("objects", payload.get("indications", [payload]))
    if not isinstance(payload, list):
        raise ValueError("object indications must be a JSON object or list")

    indications: list[ObjectIndication] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("each object indication must be a JSON object")
        bbox = item.get("bbox_xyxy")
        indications.append(
            ObjectIndication(
                name=str(item.get("name", item.get("class", "object"))),
                forward_m=float(item.get("forward_m", 0.0)),
                left_m=float(item.get("left_m", 0.0)),
                stamp_s=float(item.get("stamp_s", stamp_s)),
                confidence=float(item.get("confidence", 0.0)),
                source=str(item.get("source", "object_detector")),
                range_source=str(item.get("range_source", "bbox_size")),
                position_uncertainty_m=(
                    float(item["position_uncertainty_m"])
                    if item.get("position_uncertainty_m") is not None
                    else None
                ),
                bbox_xyxy=(
                    tuple(float(value) for value in bbox)
                    if bbox is not None and len(bbox) == 4
                    else None
                ),
            )
        )
    return indications


def object_tracks_json(
    tracker: ObjectTracker, *, now_s: float, include_expired: bool = False
) -> str:
    return json.dumps(
        tracker.payload(now_s=now_s, include_expired=include_expired),
        separators=(",", ":"),
        sort_keys=True,
    )


def _smooth(old: float, new: float, alpha: float) -> float:
    return old * (1.0 - alpha) + new * alpha


def _track_uncertainty(indication: ObjectIndication) -> float:
    if indication.position_uncertainty_m is not None:
        return max(0.0, indication.position_uncertainty_m)
    confidence_penalty = max(0.0, 1.0 - max(0.0, min(1.0, indication.confidence)))
    return 0.12 + confidence_penalty * 0.18
