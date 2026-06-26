# V5 Brain Slot Manifest

This file is the repo-side source of truth for what must be loaded into the VEX
Brain user slots. It is not physical proof by itself; physical proof requires a
connected Brain and the verification checklist below.

## Current Assignments

| Slot | Name | Brain artifact | ROS task request | Status |
|---|---|---|---|---|
| 4 | Return Home | `robot/v5-brain/pros_bridge` | `{"target":"home:tag","action":"return_home","target_distance_m":0.45,"dispatch":true}` | Assigned |
| 7 | Driver Telemetry | `robot/v5-brain/driver_telemetry` | N/A — manual V5 controller calibration; record `/vex/telemetry` + `/operator/annotation` | Assigned |

## Slot 4 Upload

The `pros_bridge/project.pros` file pins the default PROS upload metadata to
slot `4`, with the Brain program name `Slot 4 Return Home`. Use an explicit
slot flag anyway when producing physical proof:

```bash
cd robot/v5-brain/pros_bridge
pros make clean && pros make
pros upload --slot 4 \
  --name "Slot 4 Return Home" \
  --description "Slot 4 Return Home: guarded ROS bridge for home:tag" \
  --after none
```

Then run the slot on demand:

```bash
pros v5 ls-files
pros v5 run 4
```

## Physical Fact-Check Checklist

Capture these artifacts before telling the team slot 4 is loaded:

1. `pros v5 status` succeeds against the connected Brain.
2. `pros upload --slot 4 ... --after none` exits successfully.
3. `pros v5 ls-files` shows a user program in slot `4` named `Slot 4 Return Home`.
4. `pros v5 run 4` starts the Brain program.
5. The Brain screen or `pros v5 capture slot4-return-home.png` shows the guarded bridge ready message.
6. The Pi receives bridge proof on `/vex/bridge_status`, `/vex/ack`, and `/vex/telemetry`.
7. Publishing the ROS request below produces a `/task_plan/current` plan whose target is `home` and dispatchable step is `align_to_tag`:

```bash
ros2 topic pub --once /task_plan/request std_msgs/String \
  '{"data":"{\"target\":\"home:tag\",\"action\":\"return_home\",\"target_distance_m\":0.45,\"dispatch\":true}"}'
```

Only after all seven checks pass should we say "slot 4 is factually loaded and
running the return-home path."

## Slot 7 Upload

The `driver_telemetry/project.pros` file pins the default PROS upload metadata
to slot `7`, with the Brain program name `Slot 7 Driver Telemetry`. Use an
explicit slot flag anyway when producing physical proof:

```bash
cd robot/v5-brain/driver_telemetry
pros make clean && pros make
pros upload --slot 7 \
  --name "Slot 7 Driver Telemetry" \
  --description "Slot 7 Driver Telemetry: manual controller drive with JSON telemetry" \
  --after none
```

Then run the slot on demand:

```bash
pros v5 ls-files
pros v5 run 7
```

Capture these artifacts before telling the team slot 7 is loaded:

1. `pros v5 status` succeeds against the connected Brain.
2. `pros upload --slot 7 ... --after none` exits successfully.
3. `pros v5 ls-files` shows a user program in slot `7` named `Slot 7 Driver Telemetry`.
4. `pros v5 run 7` starts the Brain program.
5. The Brain screen or `pros v5 capture slot7-driver-telemetry.png` shows `slot 7 driver telemetry`.
6. The Pi receives `/vex/telemetry` with `manual_mode:true`.
7. Publishing or typing one `/operator/annotation` label records into the same bag as telemetry.
