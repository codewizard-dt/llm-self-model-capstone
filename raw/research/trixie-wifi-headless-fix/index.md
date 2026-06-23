---
topic: "What is the current fix status of the Raspberry Pi OS Trixie WiFi headless boot bug? Is Trixie now safe for headless WiFi setup on a Raspberry Pi 5?"
slug: trixie-wifi-headless-fix
researched: 2026-06-23
sources: [./sources.md]
---

# Research: Raspberry Pi OS Trixie — WiFi Headless Boot Bug Fix Status

> The Dec 2025 WiFi headless bug is **fixed**, but only for users running Raspberry Pi Imager **v2.0 or newer**. Trixie switched from `firstrun.sh` to cloud-init for first-boot provisioning (Nov 24, 2025); the old Imager (v1.9.x) silently wrote broken WiFi config because a required binary was removed from Trixie's package. With Imager v2.0+ (latest: v2.0.10, released June 19, 2026), Trixie headless WiFi works reliably on Pi 5. Trixie is now the **default and recommended** RPi OS — Bookworm is "Legacy". The wiki's guidance to use Bookworm is stale for Pi 5 + Imager 2.0+.

---

## Research Questions

1. What exactly caused the Dec 2025 Trixie WiFi headless bug?
2. Is the bug fixed in newer Trixie images, and if so, what was the fix?
3. What Imager version is required, and what is the current latest?
4. Are there any residual WiFi issues on Trixie that still affect headless Pi 5 setup?
5. Should the capstone continue to use Bookworm, or switch to Trixie?

---

## Current State (Codebase)

Not directly relevant — this is OS/toolchain setup research. The capstone uses the Pi 5 as a coprocessor; the OS image choice affects setup steps documented in the wiki at `wiki/knowledge/sources/rpi5-mac-connection.md`, which currently recommends Bookworm and warns against Trixie.

---

## Key Findings

### 1. Root Cause of the Dec 2025 Bug [S1, S2, S3]

The bug had two overlapping causes, both tied to Trixie's mid-transition state in late 2025:

**Cause A — Missing binary (Imager 1.9.x + early Trixie):** Imager v1.9.x generates a `firstrun.sh` script that calls `/usr/lib/raspberrypi-sys-mods/imager_custom set_wlan ...` to configure WiFi via NetworkManager. On Bookworm, this binary exists. On Trixie (from `raspberrypi-sys-mods_20250630_arm64.deb` onward), RPi **removed** `imager_custom` in preparation for cloud-init. When the binary was absent, `firstrun.sh` silently fell back to writing `wpa_supplicant.conf` — which NetworkManager (Trixie's default) ignores. WiFi was silently unconfigured.

**Cause B — Architecture mismatch (Imager 1.9.x + Nov 2025 Trixie):** The Nov 24, 2025 Trixie release switched to cloud-init as the first-boot provisioning system. Imager 1.9.x didn't know about cloud-init and continued writing `firstrun.sh`, which the new Trixie image couldn't process properly. The new system requires writing `user-data` and `network-config` YAML files to the boot partition.

**Additional factor — rfkill:** Trixie keeps the WiFi radio blocked via rfkill by default at first boot. The cloud-init network config includes an rfkill unblock step, but manual `wpa_supplicant.conf` workarounds fail because rfkill prevents the radio from connecting regardless of credentials.

### 2. The Fix: Imager v2.0+ [S4, S5, S6]

Raspberry Pi released **Imager v2.0** alongside the cloud-init Trixie update (Nov 24, 2025). Imager 2.0 detects Trixie images via the `"init_format": "cloudinit-rpi"` metadata field and writes cloud-init YAML (`user-data` + `network-config`) instead of `firstrun.sh`. This fully resolves both root causes.

- **Confirmed working**: Zero 2W with Imager 2.0.6+ [S7]; Pi 5 with Imager 2.0+
- **GitHub issues closed**: rpi-imager #1189 and raspberrypi-sys-mods #102 (the canonical bug reports) are both **CLOSED** [S2, S3]
- **Latest Imager**: v2.0.10, released June 19, 2026 [S8]

Imager v1.9.x (including 1.9.6) does **not** fix the issue for Trixie images — Bookworm images remain compatible with 1.9.x.

### 3. Trixie Is Now the Default OS [S9, S10]

As of 2026, Trixie is the **default and officially recommended** Raspberry Pi OS. Bookworm is now labelled "Legacy" in Pi Imager. The cloud-init announcement (Nov 2025) describes the transition as deliberate and forward-looking.

### 4. Residual Issues on Trixie (Not Headless-Setup Related) [S11, S12]

Two distinct WiFi issues remain on Trixie but are unrelated to headless first-boot setup:

- **WiFi disconnect bug (trixie-feedback #25):** On some Pi 5 setups, WiFi drops after 4–18 hours and does not auto-reconnect. This is a NetworkManager keepalive / driver issue, not a headless setup problem. Status: open as of research date.
- **AP compatibility issue on Zero 2W / Pi 3 (trixie-feedback #23):** Wireless handshake failures with certain access points; fix is `options brcmfmac roamoff=1 feature_disable=0x82000` in `/etc/modprobe.d/brcmfmac.conf`. Does **not** affect Pi 5.
- **Manual cloud-init (without Imager) is complex:** rfkill blocks WiFi before cloud-init runs; manually crafting correct cloud-init YAML is non-obvious and poorly documented. The safe path is always to use Imager 2.0+.

### 5. Capstone Recommendation [inference]

For the capstone Pi 5 + Mac headless setup:
- **With Imager 2.0.10 (current), Trixie headless WiFi on Pi 5 is fully reliable** — the original bug is fixed.
- **Bookworm still works** and is the safe conservative choice before June 29 demo.
- The wiki's current guidance ("use Bookworm, not Trixie") is now stale and should be updated.
- Both OSes support all capstone dependencies (OpenCV, pyserial, apriltag, picamera2, rpi-connect).

---

## Constraints

- Pi 5 hardware is unambiguously fixed with Imager 2.0+ — no Pi 5-specific headless WiFi bug remains.
- The WiFi disconnect bug (#25) affects already-running Pi 5 systems (hours after boot), not first-boot headless setup.
- If deploying from a Linux host with an older Imager (1.9.x via `apt`), the bug will recur — must use Imager 2.0+.
- Manual (no-Imager) cloud-init setup remains error-prone; always use Imager 2.0+ for the capstone.

---

## Recommendation

**Switch the wiki to recommend Trixie + Imager v2.0.10 for Pi 5 headless setup.** The Dec 2025 bug is definitively fixed. The procedure:

1. Download **Raspberry Pi Imager v2.0.10** (macOS `.dmg` from github.com/raspberrypi/rpi-imager/releases/tag/v2.0.10)
2. Select **Raspberry Pi OS (64-bit) — Trixie** (the current non-legacy default)
3. In OS Customisation, set hostname, username, SSH, WiFi SSID/password — Imager 2.0 writes correct cloud-init YAML
4. Flash, boot, SSH via `user@hostname.local`

**If demo is imminent (< 1 week) or the current Bookworm install is already working:** no need to switch — Bookworm remains fully supported. Plan an upgrade to Trixie post-demo.

**Risks:**
- The WiFi disconnect bug (#25) may cause runtime WiFi drops on Pi 5 during long capstone runs. Mitigation: add a systemd service or cron to reconnect if WiFi drops, or connect via Ethernet for critical runs.
- Always use 2.4 GHz for initial setup (more reliable for first connect).

---

## Next Steps

- Update `wiki/knowledge/sources/rpi5-mac-connection.md` to reflect that Trixie + Imager 2.0+ is now the recommended path.
- Consider `/wiki-ingest raw/research/trixie-wifi-headless-fix/index.md` to add a Trixie OS concept page.
- Watch trixie-feedback #25 (WiFi disconnect) if capstone runs exceed 4 hours headless.
