---
topic: "AprilTag workspace design for larger arenas: tag sizing, detection range, pose memory, and multi-map file format"
slug: apriltag-larger-workspace-map
researched: 2026-06-22
---

# Primary Sources — AprilTag Larger Workspace & Map Format

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/pi-runtime/config/defaults` | 2026-06-22 | VEXY_* env var naming pattern; VEXY_CAMERA_WIDTH=640; no map var exists yet |
| S1 | codebase | `robot/pi-runtime/src/vexy_system2/state.py` | 2026-06-22 | atomic_write_json / read_json — existing pattern for persistent JSON state |
| S1 | codebase | `robot/pi-runtime/src/vexy_system2/camera_broker.py` | 2026-06-22 | vision pipeline entry point; no localization layer yet |
| S1 | codebase | `robot/pi-runtime/src/vexy_system2/protocol.py` | 2026-06-22 | MAX_LINEAR, MAX_OMEGA, DEFAULT_TTL_MS constants; no map awareness |
| S2 | web | https://april.eecs.umich.edu/software/apriltag | 2026-06-22 | "targets can be created from an ordinary printer"; detection library is C with Python bindings; no external deps |
| S3 | web | https://github.com/AprilRobotics/apriltag | 2026-06-22 | Detection distance scales with tag size; "tag36h11" recommended family; quad_decimate=1 for max range |
| S4 | web | http://www.aerialroboticscompetition.org/assets/downloads/AprilTag_Identifiers.pdf | 2026-06-22 | "Size and Distance: This is governed by the camera's resolution. A tag must occupy a sufficient number of pixels in the image for its internal code to be decoded." |
| S5 | web | https://www.cs.cmu.edu/~kaess/pub/Westman18tr.pdf | 2026-06-22 | CMU underwater SLAM: dead reckoning drifts tens of cm over 6 min without tag fix; tag re-observation corrects it; EKF fusion pattern |
| S6 | web | https://duckietown.com/localization-with-sensor-fusion-in-duckietown/ | 2026-06-22 | "incorporating AprilTags as global reference landmarks, thereby enhancing spatial awareness in environments where dead reckoning alone is insufficient" |
| S7 | web | https://docs.limelightvision.io/docs/docs-limelight/pipeline-apriltag/apriltag-map-specification | 2026-06-22 | .fmap JSON format: type, fiducials[], each with family/id/size/transform(4x4 matrix)/unique fields; industry standard for FRC/FTC |
| S8 | web | https://docs.photonvision.org/en/latest/docs/apriltag-pipelines/multitag.html | 2026-06-22 | "field layout JSON" format; multi-tag localization uses uploaded layout to compute camera pose; format is same as WPILib field layout JSON |
| S9 | web | https://ftc-docs.firstinspires.org/en/latest/apriltag/vision_portal/apriltag_localization/apriltag-localization.html | 2026-06-22 | FTC 2024 SDK: robot global pose from AprilTag fixed landmarks; pose memory pattern via camera pose + field metadata |
| S10 | web | https://uclalemur.com/blog/determining-the-ideal-resolution-for-apriltag-detection | 2026-06-22 | 320×240 detects at similar range as 240×240; resolution tradeoff; "most area on the ground can be seen while AprilTags are still detectable" |

---

## Excerpts

### S3 — AprilRobotics/apriltag GitHub
https://github.com/AprilRobotics/apriltag
> "We recommend using the tagStandard41h12 layout... Increasing detection distance."
> "One family which has a hole in the middle. This could be used for example for drone applications by placing different sized tags inside of each other to allow detection over a wide range of distances."

### S4 — Aerial Robotics Competition: AprilTag Identifiers
http://www.aerialroboticscompetition.org/assets/downloads/AprilTag_Identifiers.pdf
> "Size and Distance: This is governed by the camera's resolution. A tag must occupy a sufficient number of pixels in the image for its internal code to be decoded."

### S5 — CMU Westman 2018: Underwater AprilTag SLAM
https://www.cs.cmu.edu/~kaess/pub/Westman18tr.pdf
> "The dead reckoning estimate clearly drifts by tens of centimeters if not meters over the course of the six-minute dataset."
> "We have presented a novel formulation of simultaneous underwater localization, mapping, and extrinsics calibration using a camera and one or more odometry sensors... We utilize AprilTag fiducials to [correct drift]."

### S6 — Duckietown: Localization with Sensor Fusion
https://duckietown.com/localization-with-sensor-fusion-in-duckietown/
> "incorporating AprilTags as global reference landmarks, thereby enhancing spatial awareness in environments where dead reckoning alone is insufficient"
> "correcting odometry drift by broadcasting transforms from estimated AprilTag poses to the Duckiebot's base frame"

### S7 — Limelight: AprilTag Map Specification
https://docs.limelightvision.io/docs/docs-limelight/pipeline-apriltag/apriltag-map-specification
> "Limelight's field-space localization feature uses .fmap files to compute a robot pose for use by WPILIB's pose estimators. Our fmap files support maps comprised of different target sizes and different families. You can use fmaps to define 'environments' such as FRC fields, or 'objects' such as objects that have several attached AprilTags."

Example fmap structure:
```json
{
  "type": "frc",
  "fiducials": [
    {
      "family": "apriltag3_36h11_classic",
      "id": 1,
      "size": 165.1,
      "transform": [-0.5, -0.866025, 0, 6.808597, 0.866025, -0.5, 0, -3.859403, 0, 0, 1, 1.355852, 0, 0, 0, 1],
      "unique": 1
    }
  ]
}
```

### S8 — PhotonVision: MultiTag Localization
https://docs.photonvision.org/en/latest/docs/apriltag-pipelines/multitag.html
> "PhotonVision can combine AprilTag detections from multiple simultaneously observed AprilTags from a particular camera with information about where tags are expected to be located on the field to produce a better estimate of where the camera (and therefore robot) is located on the field."
> "An updated field layout can be uploaded by navigating to the 'Device Control' card of the Settings tab and clicking 'Import Settings'. In the pop-up dialog, select the 'AprilTag Layout' type and choose an updated layout JSON"

### S9 — FTC Docs: AprilTag Localization
https://ftc-docs.firstinspires.org/en/latest/apriltag/vision_portal/apriltag_localization/apriltag-localization.html
> "An OpMode can also read that AprilTag's global pose (on the FTC game field), stored as metadata. This means it's possible to calculate the camera's global pose – namely its position and orientation on the game field."
> "Since 2023, an FTC OpMode can read the pose (position and orientation) of an AprilTag, relative to the camera."
