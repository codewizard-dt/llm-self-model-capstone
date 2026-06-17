---
topic: "Options for connecting to a Raspberry Pi 5 from an M5 Mac, with a Bluetooth keyboard and mouse (CanaKit Starter Kit, SD pre-installed)"
slug: rpi5-mac-connection
researched: 2026-06-17
sources: [./sources.md]
---

# Research: Connecting to a Raspberry Pi 5 from an M5 Mac

> You have a CanaKit RPi 5 with Raspberry Pi OS pre-installed on SD, an M5 Mac, and a Bluetooth keyboard/mouse. **Recommended path: use the included USB card reader to re-flash the SD with Raspberry Pi Imager (enabling SSH + WiFi), then SSH from Mac Terminal — no monitor or extra hardware needed.** For graphical access afterward, Raspberry Pi Connect is the lowest-friction option.

---

## Research Questions

1. What connection methods are available for RPi 5 (SSH, VNC, USB gadget, Pi Connect, direct)?
2. Does the CanaKit pre-installed OS have SSH enabled out of the box?
3. How do you do initial headless setup from an M5 Mac specifically?
4. How does the Bluetooth keyboard/mouse factor in for initial setup?
5. What is the best ongoing remote-access approach once the Pi is on the network?

---

## Current State (Codebase)

Not applicable — this is hardware setup research, unrelated to the capstone codebase.

---

## Key Findings

### Critical: CanaKit SD is unlikely to have SSH enabled [S1, S2]

CanaKit ships the SD pre-loaded with 64-bit Raspberry Pi OS, but standard Raspberry Pi OS does **not** enable SSH by default for security reasons. The CanaKit kit does **not** pre-enable SSH. Attempting to SSH on first boot will fail. [S2]

**However**, the CanaKit includes a **USB card reader dongle** — this is your unlock. You can insert the SD into it, connect to your Mac, and either:
- Re-flash with Raspberry Pi Imager (setting SSH + WiFi before imaging), or
- Mount the existing `bootfs` partition and drop configuration files in.

### Bluetooth keyboard/mouse requires initial pairing [inference]

Bluetooth peripherals cannot be used for the Pi's very first boot without a display — Bluetooth requires OS-level pairing (a GUI or command-line step). The BT keyboard/mouse are only useful for Day 2 use or if you have an HDMI monitor for initial setup.

### USB gadget mode works on Pi 5 but has caveats [S3, S4]

As of Raspberry Pi OS **Trixie** (images dated 20 Oct 2025+), USB gadget mode is officially supported via the `rpi-usb-gadget` package and can be enabled in Pi Imager. This lets you connect Pi → Mac via USB-C cable with no WiFi/Ethernet needed. **Caveat for M5 Mac:** The Pi 5 draws more power than a Pi 4, and Mac USB-C PD negotiation can cause issues — power instability has been reported [S4]. Works best when Pi is separately powered and USB-C is data-only.

### New Trixie OS has known WiFi headless issues [S5]

If you re-flash with the newest Trixie image (Dec 2025), there are known WiFi connectivity problems on first headless boot. Bookworm is currently more reliable for headless WiFi setup.

---

## Constraints

- SD pre-installed → SSH not enabled by default; must re-flash or edit boot partition
- No HDMI monitor mentioned → headless approach is required
- Bluetooth KB/mouse cannot substitute for wired input on first boot
- CanaKit kit **does** include USB card reader and 2× microHDMI cables
- Pi 5 USB-C power draw can conflict with M5 Mac USB-C PD

---

## Solution Comparison

| Criteria | Option A: SSH over WiFi (re-flash) | Option B: Raspberry Pi Connect | Option C: USB-C Gadget Mode | Option D: Direct HDMI + BT |
|---|---|---|---|---|
| **Approach** | Re-flash SD via Pi Imager with SSH+WiFi pre-configured; SSH from Mac Terminal | Install rpi-connect on Pi, access from any browser | Configure gadget mode; Pi appears as USB network adapter on Mac | Connect microHDMI to a TV/monitor; pair BT peripherals |
| **Pros** | Fastest path; works without any monitor; standard approach; free | No IP lookup needed; works from any device; browser-based GUI | No WiFi/router required; direct cable connection | No reflash needed; uses pre-installed OS as-is |
| **Cons** | Requires reflashing (loses pre-installed image, re-downloadable) | Requires initial SSH/network access first to install; needs internet | Pi 5 power issues with M5 Mac; needs config work; Trixie only natively | Needs HDMI display; BT pairing needed first; not mentioned in kit |
| **Complexity** | Low | Low (after SSH) | Medium–High | Low (if you have a display) |
| **Dependencies** | Raspberry Pi Imager on Mac (free) | Internet on Pi; rpi-connect package | Trixie OS or manual gadget config | HDMI monitor or TV |
| **Ongoing use** | Terminal / SSH workflows | Browser GUI + terminal from anywhere | Good for travel without WiFi | Local use only |
| **Recommendation** | **Start here** | Add this after first boot | Skip for initial setup | Use if you have a spare TV |

---

## Recommendation

### Step 1 — Initial setup (Option A)

1. **Remove the SD card** from the Pi and insert it into the included USB card reader, then plug into your Mac.
2. **Download Raspberry Pi Imager** for macOS from raspberrypi.com/software.
3. In Imager: choose **Raspberry Pi OS (64-bit) Bookworm** (not Trixie — more stable for headless WiFi as of mid-2026).
4. Click the **gear icon** (or "OS Customization") before writing:
   - Set hostname (e.g. `mypi`)
   - Set username + password
   - Enable **SSH** (password auth)
   - Enter your **WiFi SSID + password**
   - Set locale/timezone
5. Write to the SD card. Boot the Pi. Wait ~90 seconds.
6. From Mac Terminal: `ssh youruser@mypi.local` (mDNS usually resolves hostname automatically on the same network).

### Step 2 — Add graphical access (Option B)

Once SSHed in, install Raspberry Pi Connect:
```bash
sudo apt update && sudo apt install rpi-connect
rpi-connect on
```
Then visit connect.raspberrypi.com in your Mac browser — screen sharing + terminal from anywhere, no VNC client needed.

### Step 3 — Pair your Bluetooth keyboard/mouse

Once the Pi is on the network and accessible, pair BT peripherals via:
- `bluetoothctl` over SSH, or
- Raspberry Pi Connect GUI → System → Bluetooth

### Risks and Mitigations

| Risk | Mitigation |
|---|---|
| mDNS `.local` not resolving | Use `arp -a` on Mac or check router DHCP leases for Pi's IP |
| WiFi not connecting on first boot | Verify SSID/password in Imager; try 2.4 GHz band (Pi 5 supports both but 2.4 GHz is more reliable for first connect) |
| SSH connection refused | Confirm SSH was enabled in Imager settings; re-flash if unsure |
| Trixie WiFi issues | Use Bookworm image instead |

---

## Next Steps

- Flash SD with Raspberry Pi Imager using the settings above → immediate SSH access
- After SSH works: `sudo apt update && sudo apt full-upgrade` then install `rpi-connect`
- Pair BT keyboard/mouse over SSH using `bluetoothctl`
- If a display is ever needed for debugging: the kit's microHDMI cables connect directly to any TV or monitor with HDMI input
