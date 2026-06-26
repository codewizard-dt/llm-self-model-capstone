# VEXY Vision Input, Processing, and Usage

> Auto-generated from `wiki/knowledge/entities/components/vexy-ros-runtime.md` by `mermaid-flowchart` skill.

## Master Overview

```mermaid
flowchart LR
    Physical[Physical scene]
    Acquisition[Image acquisition]
    Perception[Perception]
    WorldModel[World model]
    Behavior[Behavior and control]
    Observability[Observability]

    Physical ==> Acquisition
    Acquisition ==> Perception
    Perception ==> WorldModel
    WorldModel ==> Behavior
    Acquisition -.-> Observability
    Perception -.-> Observability
    WorldModel -.-> Observability
    Behavior -.-> Observability

    classDef world fill:#e0f2fe,stroke:#0369a1,color:#111;
    classDef compute fill:#ecfdf5,stroke:#047857,color:#111;
    classDef observe fill:#f3e8ff,stroke:#7e22ce,color:#111;
    class Physical,WorldModel world;
    class Acquisition,Perception,Behavior compute;
    class Observability observe;
```

## Physical Scene

```mermaid
flowchart LR
    Arena[/Arena\]
    Tags[/AprilTags\]
    Ball[/Yellow ball\]
    Robot[/Robot and claw\]
    Map[(Workspace map)]
    Camera[/Pi Camera Module 3\]
    Task[/Task request\]

    Arena --> Tags
    Arena --> Ball
    Robot --> Camera
    Tags --> Camera
    Ball --> Camera
    Map -->|static layout| WorldModel[World model]
    Task -->|goal| Behavior[Behavior]

    classDef physical fill:#e0f2fe,stroke:#0369a1,color:#111;
    classDef data fill:#fef3c7,stroke:#b45309,color:#111;
    class Arena,Tags,Ball,Robot,Camera physical;
    class Map,Task,WorldModel,Behavior data;
```

## Image Acquisition

```mermaid
flowchart LR
    Camera[/Pi Camera Module 3\]
    Calibration[(CameraInfo YAML)]
    CameraRos(camera_ros)
    RawImage{{/camera/image_raw}}
    CameraInfo{{/camera/camera_info}}
    ImageProc(image_proc)
    RectImage{{/camera/image_rect}}

    Camera -->|frames| CameraRos
    Calibration -->|camera_info_url| CameraRos
    CameraRos --> RawImage
    CameraRos --> CameraInfo
    RawImage ==> ImageProc
    CameraInfo ==> ImageProc
    ImageProc -->|rectified| RectImage

    classDef input fill:#e0f2fe,stroke:#0369a1,color:#111;
    classDef process fill:#ecfdf5,stroke:#047857,color:#111;
    classDef topic fill:#fef3c7,stroke:#b45309,color:#111;
    class Camera,Calibration input;
    class CameraRos,ImageProc process;
    class RawImage,CameraInfo,RectImage topic;
```

## Perception

```mermaid
flowchart LR
    RectImage{{/camera/image_rect}}
    CameraInfo{{/camera/camera_info}}
    AprilTag(apriltag_ros)
    TagPose{{"tag detections + /tf"}}
    BallDetector(yellow_ball_detector)
    Yolo(YOLO NCNN)
    ObjectBoxes{{/vision/object_detections}}
    ObjectProjector(object_indication)
    ObjectHints{{/vision/object_indications}}

    RectImage ==> AprilTag
    CameraInfo --> AprilTag
    AprilTag --> TagPose
    RectImage --> BallDetector
    RectImage -.-> Yolo
    BallDetector --> ObjectBoxes
    Yolo -.-> ObjectBoxes
    ObjectBoxes --> ObjectProjector
    CameraInfo --> ObjectProjector
    ObjectProjector --> ObjectHints

    classDef process fill:#ecfdf5,stroke:#047857,color:#111;
    classDef topic fill:#fef3c7,stroke:#b45309,color:#111;
    class AprilTag,BallDetector,Yolo,ObjectProjector process;
    class RectImage,CameraInfo,TagPose,ObjectBoxes,ObjectHints topic;
```

## World Model

```mermaid
flowchart LR
    TagPose{{"tag poses"}}
    ObjectHints{{"object hints"}}
    WorkspaceMap[(Workspace map)]
    SceneMap(scene_map)
    RobotPose{{"robot pose"}}
    ObjectPose{{"object estimates"}}
    SceneTopic{{/vision/scene_map}}
    Planner[task_plan]

    TagPose ==> SceneMap
    ObjectHints --> SceneMap
    WorkspaceMap --> SceneMap
    SceneMap --> RobotPose
    SceneMap --> ObjectPose
    RobotPose --> SceneTopic
    ObjectPose --> SceneTopic
    SceneTopic --> Planner

    classDef input fill:#e0f2fe,stroke:#0369a1,color:#111;
    classDef process fill:#ecfdf5,stroke:#047857,color:#111;
    classDef topic fill:#fef3c7,stroke:#b45309,color:#111;
    class WorkspaceMap input;
    class SceneMap,Planner process;
    class TagPose,ObjectHints,RobotPose,ObjectPose,SceneTopic topic;
```

## Behavior And Control

```mermaid
flowchart LR
    TaskRequest[/Task request\]
    SceneTopic{{/vision/scene_map}}
    TaskPlan(task_plan)
    LocalSkill("align_to_tag / survey_scan")
    VexCmd{{/vex/cmd}}
    VexBridge(vex_bridge)
    Brain[VEX V5 Brain]
    Motors[/Drive + effector motors\]
    Feedback{{"acks + telemetry"}}

    TaskRequest --> TaskPlan
    SceneTopic --> TaskPlan
    TaskPlan -->|bounded goal| LocalSkill
    LocalSkill --> VexCmd
    VexCmd --> VexBridge
    VexBridge -->|serial JSON| Brain
    Brain --> Motors
    Brain --> Feedback

    classDef input fill:#e0f2fe,stroke:#0369a1,color:#111;
    classDef process fill:#ecfdf5,stroke:#047857,color:#111;
    classDef topic fill:#fef3c7,stroke:#b45309,color:#111;
    classDef output fill:#f3e8ff,stroke:#7e22ce,color:#111;
    class TaskRequest,Motors input;
    class TaskPlan,LocalSkill,VexBridge process;
    class SceneTopic,VexCmd,Feedback topic;
    class Brain output;
```

## Observability

```mermaid
flowchart LR
    CameraTopics{{"camera topics"}}
    PerceptionTopics{{"perception topics"}}
    SceneTopic{{/vision/scene_map}}
    CommandTopics{{"commands + feedback"}}
    Foxglove((Foxglove browser))
    Mcap[(MCAP recording)]
    Jsonl[(contract JSONL)]

    CameraTopics -.-> Foxglove
    PerceptionTopics -.-> Foxglove
    SceneTopic -.-> Foxglove
    CameraTopics -.-> Mcap
    PerceptionTopics -.-> Mcap
    SceneTopic -.-> Mcap
    CommandTopics -.-> Mcap
    Mcap --> Jsonl

    classDef topic fill:#fef3c7,stroke:#b45309,color:#111;
    classDef output fill:#f3e8ff,stroke:#7e22ce,color:#111;
    class CameraTopics,PerceptionTopics,SceneTopic,CommandTopics topic;
    class Foxglove,Mcap,Jsonl output;
```

## Notes

- Every Mermaid chart in this file has nine nodes or fewer.
- The grouping follows natural runtime boundaries: physical scene, image acquisition, perception, world model, behavior/control, and observability.
- `yellow_ball_detector` is the default object detector; `yolo_ncnn` is optional and disabled until a model path is supplied.
- Object indications are coarse camera-relative hints, not proof that a ball is inside the claw.
- The calibrated AprilTag path depends on `camera_info_url`, `/camera/camera_info`, and rectified `/camera/image_rect` being valid.
