# V5 Brain Toolchain Setup

> This is the **terse setup runbook**. For the detailed bring-up story — every gotcha we
> hit (CLI-on-Python-3.13, the hot/cold→monolith saga, COBS, the two serial ports,
> `pros::screen` vs `pros::lcd`) and the verified working state — see
> [BRINGUP.md](BRINGUP.md). For the Pi↔Brain interface, see
> [../pi-runtime/docs/BRAIN_INTERFACE.md](../pi-runtime/docs/BRAIN_INTERFACE.md).

## Prerequisites

- macOS (arm64 or x86_64)
- Python 3.11+
- Homebrew

---

## 1. ARM cross-compiler

PROS compiles for the VEX V5 Brain's ARM Cortex-A9. You need the `arm-none-eabi` toolchain.

```bash
brew install --cask gcc-arm-embedded
```

This installs a `.pkg` via `sudo` — run it in an interactive terminal (not a background shell).

Verify:

```bash
arm-none-eabi-g++ --version
```

---

## 2. PROS CLI

The PROS CLI lives in a local venv. This project uses **uv** for all Python package
management — never `pip`/`pipx`. `pros-cli` is pinned in `pyproject.toml` + `uv.lock`,
so `uv sync` reproduces the environment:

```bash
uv venv          # create .venv
uv sync          # install pros-cli (and any other pinned deps)
```

(To add a new dependency: `uv add <package>`, then `uv sync`.)

### Python 3.13 version-detection bug

`pros-cli 3.5.6` uses a deprecated `pkg_resources` API that crashes on Python 3.13
with `RuntimeError: Could not determine version`. Fix it by dropping a `version` file
where the code looks for it:

```bash
echo "3.5.6" > .venv/lib/python3.*/site-packages/version
```

Verify:

```bash
source .venv/bin/activate
pros --version   # should print: pros, version 3.5.6
```

---

## 3. Create a new PROS project

```bash
source .venv/bin/activate
pros conductor new-project <project-name> v5
```

This downloads `kernel` and `liblvgl` from the pros-mainline depot, scaffolds the
project, and runs an initial build. Both the ARM toolchain and an active internet
connection are required.

### Fresh clone of an existing project

`firmware/` and `include/` are gitignored (they are depot-managed artifacts). After
cloning, restore them with:

```bash
source .venv/bin/activate
cd <project-name>
pros conductor apply
```

---

## 4. Build and upload

```bash
cd <project-name>
pros build
pros upload          # V5 Brain must be connected via USB
```

Check status / connected device:

```bash
pros v5 status        # firmware + connection info (there is no `lsusb` subcommand)
```

---

## 5. CRITICAL: build as a monolith, not hot/cold

By default PROS uses **hot/cold linking** (`USE_PACKAGE:=1` in `Makefile`): the PROS
kernel + libraries ("cold package") are uploaded once, and only your code ("hot
package") is re-uploaded each time. On this Brain (VEXos 1.1.5.0) the hot/cold split
was **silently broken**:

- The program would *appear* to run (program name + timer on the Brain screen) but
  **nothing rendered and zero serial bytes came out** — both display and `printf`/
  `stderr` were dead.
- The compiled code was correct (verified by disassembly). The hot package's calls
  go through *veneers* that jump to fixed addresses in the onboard cold package.
- `pros upload` kept printing **"Library is already onboard V5"** — a false positive.
  The onboard cold package did not match the hot package's veneer addresses, so every
  library call (`printf`, `pros::screen::*`, serial) jumped to the wrong address and
  silently no-op'd. `pros v5 rm-all` does **not** clear the library, and there is no
  force-library flag.

**Fix — build a monolith** (everything linked into one binary, no veneers, no
separate library):

```makefile
# Makefile
USE_PACKAGE:=0
```

```bash
pros make clean && pros make    # produces bin/monolith.bin
pros upload --after run
```

Trade-off: every upload re-sends the full ~425 KB binary instead of a small hot
package. For this project that is negligible and worth the reliability.

---

## 6. Verify serial output

After upload, the Brain emits COBS-framed packets on the **user** USB port
(`/dev/cu.usbmodem*3` on macOS; system/upload port ends in `1`).

```bash
pros terminal        # decodes COBS, shows stdout/stderr (run in an interactive shell)
```

`std::printf(...)` + `std::fflush(stdout)` → arrives as a `sout` packet. `stderr` is
guaranteed-delivery and arrives as `serr`. For a raw Pi-side reader, add
`pros::c::serctl(SERCTL_DISABLE_COBS, NULL)` so frames are plain newline-delimited
text (note: this breaks `pros terminal`, which expects COBS).
