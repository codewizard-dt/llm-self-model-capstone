---
topic: Does the PROS CLI (pip install pros-cli) work on ARM64 Linux (Ubuntu 24.04, Raspberry Pi 5)?
slug: pros-cli-arm64-pi
researched: 2026-06-25
---

# Primary Sources — PROS CLI on ARM64 Linux

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://pypi.org/project/pros-cli/ | 2026-06-25 | Wheel filename `pros_cli-3.5.6-py3-none-any.whl` confirming pure Python (no native extensions, any platform) |
| S2 | codebase | `robot/v5-brain/TOOLCHAIN.md` | 2026-06-25 | Confirms build (arm-none-eabi-gcc) and upload are separate steps; confirms `uv sync` as the correct install path; documents Python 3.13 version-detection bug (not applicable to Pi's 3.12.3); documents hot/cold → monolith fix |
| S3 | live-system | SSH to `vexy@vexy.local` — `which pros prosv5; pip3 show pros-cli; uv tool list; uname -m` | 2026-06-25 | Confirmed: PROS CLI not installed, uv not installed, arm-none-eabi-gcc not installed, Pi is aarch64, Python 3.12.3 |
| S4 | live-system | SSH to `vexy@vexy.local` — `ls robot/v5-brain/pros_bridge/bin/` | 2026-06-25 | Confirmed `monolith.bin` exists pre-built on Pi |
| S5 | live-system | SSH to `vexy@vexy.local` — `cat robot/v5-brain/pros_bridge/project.pros` | 2026-06-25 | Kernel template path is `/Users/kelly/...` (macOS); `upload_options: {}` (no slot pinned) |
| S6 | live-system | SSH to `vexy@vexy.local` — `groups; ls -la /dev/ttyACM*` | 2026-06-25 | `vexy` user in `dialout` group; `/dev/ttyACM0` and `/dev/ttyACM1` present (Brain connected) |
| S7 | codebase | `robot/v5-brain/pyproject.toml` | 2026-06-25 | `dependencies = ["pros-cli>=3.5.6"]`; confirms `uv sync` installs pros-cli |
| S8 | local-tool | `pros upload --help` (from dev-machine venv) | 2026-06-25 | Full flag list: `[PATH]` accepts file or directory; `--slot INTEGER [1-8]`; `--target v5`; `--project PATH`; `--after [run\|screen\|none]`; auto-detects port |

## Excerpts

### S1 — PyPI: pros-cli
https://pypi.org/project/pros-cli/
> Details for the file **pros_cli-3.5.6-py3-none-any.whl**

`py3-none-any` = Python 3 any version, no ABI, any platform. Confirms zero native compiled extensions.

### S2 — TOOLCHAIN.md (excerpt: PROS CLI install)
`robot/v5-brain/TOOLCHAIN.md` lines ~40–60
> The PROS CLI lives in a local venv. This project uses **uv** for all Python package management — never `pip`/`pipx`. `pros-cli` is pinned in `pyproject.toml` + `uv.lock`, so `uv sync` reproduces the environment:
> ```bash
> uv venv          # create .venv
> uv sync          # install pros-cli (and any other pinned deps)
> ```
> ### Python 3.13 version-detection bug
> `pros-cli 3.5.6` uses a deprecated `pkg_resources` API that crashes on Python 3.13 with `RuntimeError: Could not determine version`.

### S5 — project.pros (upload_options excerpt)
`robot/v5-brain/pros_bridge/project.pros` (JSON)
> `"upload_options": {}` — no default slot is pinned. Must be supplied on command line.
> `"location": "/Users/kelly/Library/Application Support/PROS/templates/kernel@4.2.2"` — macOS path; does not affect upload, only build.

### S8 — pros upload --help (local dev venv)
```
Usage: pros upload [OPTIONS] [PATH] [PORT]

[PATH] may be a directory or file. If a directory, finds a PROS project root
and uploads the binary for the correct target automatically. If a file, then
the file is uploaded. Note that --target must be specified in this case.

Options:
  --target  [v5|cortex]
  --project PATH              PROS Project directory or file [default: .]
  --after -af [run|screen|none]  Action to perform on the brain after upload.
  --slot   INTEGER RANGE [1<=x<=8]  Program slot on the GUI.
  --name   TEXT               Change the name of the program.
  --after  [run|screen|none]
```
