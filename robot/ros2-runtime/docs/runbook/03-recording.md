# Recording Sessions

---

### Start a bag recording

```bash
# Record all topics, named by date/time
ros2 bag record -a -o session_$(date +%Y%m%d_%H%M%S)
```

Record specific topics only (smaller files):

```bash
ros2 bag record /camera/image_raw /camera/camera_info /camera/image_rect /apriltag/detections /tf /vision/scene_map /align_to_tag/feedback /align_to_tag/result /vex/cmd /vex/ack /vex/telemetry /vex/bridge_status \
  -o session_$(date +%Y%m%d_%H%M%S)
```

Stop with `Ctrl+C`. The bag is written to the current directory as `session_YYYYMMDD_HHMMSS/`.

### Naming convention

```
session_YYYYMMDD_HHMMSS/
  metadata.yaml
  session_YYYYMMDD_HHMMSS_0.mcap
```

Example: `session_20260623_143012/`

Store bags in `~/bags/` on the Pi:

```bash
mkdir -p ~/bags
ros2 bag record -a -o ~/bags/session_$(date +%Y%m%d_%H%M%S)
```

### Copy bags to laptop

```bash
# From laptop:
scp -r vexy@vexy.local:~/bags/session_20260623_143012 .
```

### Export VEX bridge topics and scene map to JSON for LLM analysis

Extract `/vision/scene_map`, `/vex/ack`, `/vex/telemetry`, and
`/vex/bridge_status` messages to newline-delimited JSON:

```bash
ros2 bag convert \
  --input-bagfile session_20260623_143012 \
  --output-bagfile /tmp/telem_only \
  --output-storage sqlite3

# Then extract the string payloads:
ros2 bag play session_20260623_143012 --topics /vision/scene_map /vex/ack /vex/telemetry /vex/bridge_status &
ros2 topic echo /vex/ack | while IFS= read -r line; do
  echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',''))"
done > ack_$(date +%Y%m%d_%H%M%S).jsonl
```

Simpler one-liner (plays bag and writes JSONL):

```bash
ros2 bag play session_20260623_143012 --topics /vision/scene_map /vex/ack /vex/telemetry /vex/bridge_status --rate 10 &
PLAY_PID=$!
ros2 topic echo --csv /vex/ack > ack_raw.csv
kill $PLAY_PID
# Column 2 of ack_raw.csv is the JSON string; strip it with:
awk -F',' 'NR>1 {gsub(/^"|"$/, "", $2); print $2}' ack_raw.csv > ack.jsonl
```

### Export contract-valid JSONL

For `vexy_tag_action_proof` runs, export directly from the proof directory. The
command reads `summary.json`, uses `scene_map.final.json` when present, writes
`tag_action_bundle.json`, and writes contract JSONL under `contract/`:

```bash
PYTHONPATH=/home/vexy/llm-self-model-capstone/contracts/src:$PYTHONPATH \
  ros2 run vexy_ros vexy_export_contract_jsonl \
  --proof-dir proof/tag-approach-scan-YYYYMMDD-HHMMSS \
  --no-validate
```

Use `--no-validate` on the Pi when the full `contracts` dependency environment
is not installed there; validate the copied JSONL from a repo checkout with
`uv` as shown below.

For manually assembled proof bundles, create a JSON containing the final
`/vision/scene_map` message, the terminal `/align_to_tag/result`, at least one
V5 motor sample, and the raw bag path. Then export it:

```bash
PYTHONPATH=/home/vexy/llm-self-model-capstone/contracts/src:$PYTHONPATH \
  ros2 run vexy_ros vexy_export_contract_jsonl \
  proof/align_to_tag_bundle.json \
  --out proof/contract/session_$(date +%Y%m%d_%H%M%S).jsonl
```

Validate from the repo checkout:

```bash
cd /home/vexy/llm-self-model-capstone
uv run --project contracts python - <<'PY'
from pathlib import Path
from contracts import ContractLine
for line in Path("proof/contract").glob("*.jsonl"):
    for raw in line.read_text().splitlines():
        ContractLine.model_validate_json(raw)
print("OK contract JSONL")
PY
```
