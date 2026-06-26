---
topic: "how to reduce OpenCV camera calibration RMS reprojection error for IMX708 Wide on Raspberry Pi with ROS 2 — or alternative calibration methods"
slug: camera-calibration-rms-reduction
researched: 2026-06-26
---

# Primary Sources — Camera Calibration RMS Reduction

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | codebase | `robot/ros2-runtime/src/vexy_ros/camera_calibration_capture.py::CheckerboardCalibrator` | 2026-06-26 | Current calibration implementation; calibration result showing cx=421.65 vs expected 320 |
| S2 | web | https://github.com/christianrauch/camera_ros | 2026-06-26 | camera_ros exposes libcamera controls as ROS params; pointer to CameraInfoManager and `~/set_camera_info` |
| S3 | web | https://forums.raspberrypi.com/viewtopic.php?t=354442 | 2026-06-26 | RPi forum: to force focus on Camera Module 3, must edit tuning file to misspell "rpi.af", then use v4l2-ctl |
| S4 | web | https://forums.raspberrypi.com/viewtopic.php?t=353887 | 2026-06-26 | RPi forum: libcamera AF can be disabled by removing/misspelling "rpi.af" section in imx708.json |
| S5 | web | https://libcamera.org/api-html/namespacelibcamera_1_1controls.html | 2026-06-26 | Libcamera docs: "LensPosition control is ignored unless AfMode is set to AfModeManual" |
| S6 | web | https://forums.raspberrypi.com/viewtopic.php?t=345325&start=150 | 2026-06-26 | RPi forum: dtoverlay=imx708,vcm=0 disables VCM driver entirely; wide lens focus formula: 425+14/distance |
| S7 | web | https://www.arducam.com/arducam-12mp-imx708-fixed-focus-hdr-high-snr-camera-module-for-raspberry-pi.html | 2026-06-26 | Arducam fixed-focus IMX708 variant: "A fixed focus supplement to the Raspberry Pi IMX708 autofocus camera module 3" |
| S8 | web | https://alphapixeldev.com/opencv-tutorial-part-1-camera-calibration/ | 2026-06-26 | "reprojection error of less than 0.5 pixels is considered good, while a value below 1 pixel is generally acceptable" |
| S9 | web | https://nikolasent.github.io/computervision/opencv/calibration/2024/12/20/Practical-OpenCV-Refinement-Techniques.html | 2026-06-26 | Practical OpenCV calibration tips: board flatness, distortion model selection, iterative refinement |
| S10 | web | https://docs.opencv.org/4.x/d7/d21/tutorial_interactive_calibration.html | 2026-06-26 | OpenCV interactive calibration: frame quality scoring based on scene coverage + RMS per-frame |
| S11 | web | https://www.oklab.com/blog/charuco-calibration-boards-complete-guide-to-professional-camera-calibration | 2026-06-26 | ChArUco: "With ChArUco, partial visibility works perfectly" — enables edge/corner captures |
| S12 | web | https://docs.opencv.org/4.13.0/da/d13/tutorial_aruco_calibration.html | 2026-06-26 | OpenCV docs: "recommended use of ChAruco boards instead of ArUco boards for camera calibration, since ChArUco corners are more accurate than marker corners" |
| S13 | web | https://developer.mamezou-tech.com/en/robotics/vision/calibration-pattern/ | 2026-06-26 | Accuracy ranking: "CircleGrid = Asymmetry-CircleGrid > CheckerBoard ≧ ChArUco" |
| S14 | web | https://stackoverflow.com/questions/5987285/what-is-an-acceptable-return-value-from-cvcalibratecamera | 2026-06-26 | "should be between 0.1 and 1.0 pixels in a good calibration" |
| S15 | web | https://index.ros.org/p/camera_calibration/ | 2026-06-26 | ROS camera_calibration: swap of cols/rows changed RMS from 13.5px to 0.09px |

## Excerpts

### S3 — RPi forum: forcing focus on Camera Module 3
https://forums.raspberrypi.com/viewtopic.php?t=354442
> To calibrate a camera or use fixed hardware settings: This has got a little harder than it used to be. You'll need to edit the tuning file and temporarily mis-spell "rpi.af", to stop libcamera messing with focus; then you can set the hardware lens control using v4l2-ctl

### S4 — RPi forum: disabling AF via tuning file
https://forums.raspberrypi.com/viewtopic.php?t=353887
> libcamera's AF algorithm (which is what generates lens settings, even in "manual" mode) can be disabled! Take a copy of the "imx708.json" tuning file, and remove the "rpi.af" section, or simply insert a typo to the string "rpi.af".

### S5 — libcamera LensPosition control
https://libcamera.org/api-html/namespacelibcamera_1_1controls.html
> The LensPosition control is ignored unless the AfMode is set to AfModeManual, though the value is reported back unconditionally in all modes.

### S6 — dtoverlay=imx708,vcm=0 and wide lens formula
https://forums.raspberrypi.com/viewtopic.php?t=345325&start=150
> If you manually load the overlay with "dtoverlay=imx708,vcm=0" and removing "camera_auto_detect=1", then the VCM driver will be disabled and you should be safe to "fix" it through whatever means you choose.
> It varies a little between cameras (in AF modes, this gets corrected by feedback), but the formula is roughly 450+32/distance for standard lens, or 425+14/distance for the wide one.

### S8 — Acceptable RMS values
https://alphapixeldev.com/opencv-tutorial-part-1-camera-calibration/
> A lower reprojection error indicates a more accurate calibration. As a general rule, a reprojection error of less than 0.5 pixels is considered good, while a value below 1 pixel is generally acceptable for many applications.

### S11 — ChArUco and edge coverage
https://www.oklab.com/blog/charuco-calibration-boards-complete-guide-to-professional-camera-calibration
> You need data from the image edges where distortion hits hardest. But with a traditional checkerboard, you have a problem. Move the board to capture those edge regions, and part of it leaves the frame. Detection fails. You lose that critical data. With ChArUco, partial visibility works perfectly.

### S13 — Accuracy ranking of calibration patterns
https://developer.mamezou-tech.com/en/robotics/vision/calibration-pattern/
> Regarding accuracy, the following trends are observed: CircleGrid = Asymmetry-CircleGrid > CheckerBoard ≧ ChArUco

### S14 — Acceptable RMS for calibrateCamera
https://stackoverflow.com/questions/5987285/what-is-an-acceptable-return-value-from-cvcalibratecamera
> cv::calibrateCamera() returns the root mean square (RMS) reprojection error and should be between 0.1 and 1.0 pixels in a good calibration. For a point of reference, I get approximately 0.25 px RMS error using my custom stereo camera made of two hardware-synchronized Playstation Eye cameras running at the 640 x 480 resolution.

### S15 — ROS camera_calibration cols/rows order
https://index.ros.org/p/camera_calibration/
> camera_checker: Ensure cols + rows are in correct order. Without this commit, specifying a smaller column than row size led to huge reported errors:
> $ rosrun camera_calibration cameracheck.py --size 6x7 --square 0.0495 Linearity RMS Error: 13.545 Pixels
> $ rosrun camera_calibration cameracheck.py --size 7x6 --square 0.0495 Linearity RMS Error: 0.092 Pixels
