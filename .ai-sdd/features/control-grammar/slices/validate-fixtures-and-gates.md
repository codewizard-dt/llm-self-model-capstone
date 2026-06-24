# Slice: validate-fixtures-and-gates

| Field | Value |
|---|---|
| Feature | control-grammar (F19) |
| Stack | contracts |
| Depends on | `models-and-schemas` |

## What this slice delivers

The three control-command fixtures, the additive `validate.py` dispatch that round-trips them per the `type` discriminator, the exhaustive `FaultCode` coverage assertion, and the full no-regression sweep proving F1/F2/F3/F4 still pass. This closes F19 for `m1`. Strictly additive in spirit, with **one principled glob narrowing** noted below.

## Files to create / change

```
contracts/
  fixtures/
    control_command_grab_cycle.jsonl       NEW — claw build cycle (heartbeat → drive → arm → claw → arm → stop), each followed by its ack
    control_command_flywheel_cycle.jsonl   NEW — flywheel build cycle (heartbeat → drive → flywheel(spin) → flywheel(rpm=0) → stop), each followed by its ack
    control_command_rejections.jsonl       NEW — one rejected ack per FaultCode value (exhaustive coverage)
  src/contracts/
    validate.py                            CHANGE — narrow F1 glob to session_*.jsonl + add control_command_*.jsonl dispatch (per-line type routing)
  tests/
    test_validate.py                       CHANGE — cover the new dispatch + the exhaustive FaultCode coverage assertion + the glob-narrowing invariant
```

The root `Makefile` already delegates `sync`/`validate`/`test`/`lint`/`schema`/`catalog` — **no new targets**. F19's surface lands inside the existing `make schema` (slice 1) + `make validate` (this slice) targets.

## `validate.py` changes

The existing dispatch globs `fixtures/*.jsonl` and tries every line as `ContractLine`. Adding `control_command_*.jsonl` under the same glob would force `ContractLine` to parse command/ack lines and fail. The fix is **one principled narrowing** of F1's glob, plus the new dispatch:

1. **Narrow F1's glob**: `fixtures_dir.glob("*.jsonl")` → `fixtures_dir.glob("session_*.jsonl")`. This matches the existing fixture name (`session_example.jsonl`), the canonical telemetry file pattern referenced throughout MASTER ("`session_*.jsonl`"), and mirrors F2's `self_model_*.json` family-glob style. **Behavioral no-op for the committed fixtures** (only `session_example.jsonl` exists today).
2. **Add the F19 dispatch (fourth)**, AFTER the F3 dispatch:
   ```python
   control_fixtures = (
       sorted(fixtures_dir.glob("control_command_*.jsonl")) if fixtures_dir.is_dir() else []
   )
   for path in control_fixtures:
       for lineno, raw in enumerate(path.read_text().splitlines(), 1):
           line = raw.strip()
           if not line:
               continue
           try:
               obj = json.loads(line)
               if obj.get("type") == "ack":
                   AckLine.model_validate(obj)
               else:
                   TypeAdapter(ControlLine).validate_python(obj)
           except Exception as exc:
               errors.append(f"{path.name}:{lineno}: {exc}")
   ```
   Per-line type-routed dispatch — `type == "ack"` → `AckLine`; otherwise → `ControlLine` (which itself routes `type == "cmd"` to the inner `cmd` discriminator and `type == "heartbeat"` to `HeartbeatLine`). Use `pydantic.TypeAdapter` if `ControlLine` is a discriminated-union type alias (slice 1's choice).

## Fixtures

Each fixture is newline-delimited JSON, append-only, alternating **command** (or `heartbeat`) lines with their matching **`ack`** lines. Every command's `ttl_ms ≤ TTL_MS_MAX`; every value within its `Field` bounds. `seq` monotonic per fixture.

### `control_command_grab_cycle.jsonl` — claw build (`2drive+1arm+1claw`)

```
{"v":1,"seq":1,"type":"heartbeat","sent_ms":1781880000000,"ttl_ms":200}
{"v":1,"type":"ack","ack":1,"state":"ok","recv_ms":1781880000010,"fault":null}
{"v":1,"seq":2,"type":"cmd","cmd":"drive","sent_ms":1781880000020,"ttl_ms":200,"vx":0.10,"vy":0.0,"omega":0.0}
{"v":1,"type":"ack","ack":2,"state":"ok","recv_ms":1781880000030,"fault":null}
{"v":1,"seq":3,"type":"cmd","cmd":"arm","sent_ms":1781880000040,"ttl_ms":500,"deg":90.0}
{"v":1,"type":"ack","ack":3,"state":"ok","recv_ms":1781880000050,"fault":null}
{"v":1,"seq":4,"type":"cmd","cmd":"claw","sent_ms":1781880000060,"ttl_ms":300,"state":"close"}
{"v":1,"type":"ack","ack":4,"state":"ok","recv_ms":1781880000070,"fault":null}
{"v":1,"seq":5,"type":"cmd","cmd":"arm","sent_ms":1781880000080,"ttl_ms":500,"deg":270.0}
{"v":1,"type":"ack","ack":5,"state":"ok","recv_ms":1781880000090,"fault":null}
{"v":1,"seq":6,"type":"cmd","cmd":"stop","sent_ms":1781880000100,"ttl_ms":100,"reason":"operator"}
{"v":1,"type":"ack","ack":6,"state":"ok","recv_ms":1781880000110,"fault":null}
```

### `control_command_flywheel_cycle.jsonl` — flywheel build (`2drive+1flywheel`)

```
{"v":1,"seq":1,"type":"heartbeat","sent_ms":1781881000000,"ttl_ms":200}
{"v":1,"type":"ack","ack":1,"state":"ok","recv_ms":1781881000010,"fault":null}
{"v":1,"seq":2,"type":"cmd","cmd":"drive","sent_ms":1781881000020,"ttl_ms":200,"vx":0.10,"vy":0.0,"omega":0.0}
{"v":1,"type":"ack","ack":2,"state":"ok","recv_ms":1781881000030,"fault":null}
{"v":1,"seq":3,"type":"cmd","cmd":"flywheel","sent_ms":1781881000040,"ttl_ms":1000,"rpm":2400.0}
{"v":1,"type":"ack","ack":3,"state":"ok","recv_ms":1781881000050,"fault":null}
{"v":1,"seq":4,"type":"cmd","cmd":"flywheel","sent_ms":1781881000060,"ttl_ms":1000,"rpm":0.0}
{"v":1,"type":"ack","ack":4,"state":"ok","recv_ms":1781881000070,"fault":null}
{"v":1,"seq":5,"type":"cmd","cmd":"stop","sent_ms":1781881000080,"ttl_ms":100,"reason":"operator"}
{"v":1,"type":"ack","ack":5,"state":"ok","recv_ms":1781881000090,"fault":null}
```

### `control_command_rejections.jsonl` — one rejected ack per `FaultCode`

```
{"v":1,"type":"ack","ack":100,"state":"rejected","recv_ms":1781882000000,"fault":"malformed_json"}
{"v":1,"type":"ack","ack":101,"state":"rejected","recv_ms":1781882000010,"fault":"unknown_command"}
{"v":1,"type":"ack","ack":102,"state":"stale","recv_ms":1781882000020,"fault":"ttl_expired"}
{"v":1,"type":"ack","ack":103,"state":"rejected","recv_ms":1781882000030,"fault":"watchdog"}
{"v":1,"type":"ack","ack":104,"state":"rejected","recv_ms":1781882000040,"fault":"estop_latched"}
{"v":1,"type":"ack","ack":105,"state":"rejected","recv_ms":1781882000050,"fault":"out_of_range"}
{"v":1,"type":"ack","ack":106,"state":"rejected","recv_ms":1781882000060,"fault":"oversized_packet"}
{"v":1,"type":"ack","ack":107,"state":"rejected","recv_ms":1781882000070,"fault":"not_assembled"}
```

The `ttl_expired` row uses `state: "stale"` (D6's distinction); all others use `rejected`. Every `FaultCode` value appears exactly once — the exhaustive-coverage assertion below counts them.

## Acceptance

1. `make sync` exits 0.
2. `make lint` exits 0.
3. `make validate` exits 0 — round-trips all three control fixtures through their `type`-dispatched models **and** still validates the F1 `session_*.jsonl`, F2 `self_model_*.json`, F3 `parts_catalog.json` (+ F2 fixture buildability) paths.
4. `make test` exits 0, covering at minimum these cases in `tests/test_validate.py` (additive — do not delete F1/F2/F3 cases):
   - **Exhaustive FaultCode coverage**: read `control_command_rejections.jsonl`, parse every `fault` value, and assert the set equals `{fc.value for fc in FaultCode}` — every enum value present, no extras, no duplicates.
   - **Type-routing correctness**: a `control_command_*.jsonl` line with `type: "cmd"`, `cmd: "drive"`, `vx: 0.9` (> `MAX_LINEAR`) is reported by `validate.main()` as `<file>:<lineno>: <ValidationError>` and `main()` returns 1.
   - **Glob-narrowing invariant**: `validate.main()` parses `session_example.jsonl` as `ContractLine` (unchanged behavior) and does **not** attempt to parse `control_command_*.jsonl` lines as `ContractLine` (so a deliberately broken-as-ContractLine but valid-as-ControlLine line in `control_command_*.jsonl` doesn't trigger a `ContractLine` error). Tested by mutating a copy of a control fixture in a temp dir and asserting the only errors mention `ControlLine` / `AckLine`, never `ContractLine`.
   - **Cross-dispatch isolation**: a temporarily mutated `control_command_grab_cycle.jsonl` line with `cmd: "fly"` makes `make validate` exit non-zero with a readable reason; the committed fixtures stay clean.
5. Root `make sync`/`validate`/`test`/`lint`/`schema`/`schema-check`/`catalog`/`catalog-check` all exit 0.
6. The full F1 + F2 + F3 + F4 test suites still pass (no regression); `make test` green at contracts + root.
