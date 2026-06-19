---
id: rpi5-mac-connection
title: Research — Connecting to a Raspberry Pi 5 from an M5 Mac (CanaKit, Headless)
updated: 2026-06-17
sources:
  - ../../raw/research/rpi5-mac-connection/index.md
tags: [raspberry-pi, setup, mac, ssh, headless, hardware]
---

# Research: Connecting to a Raspberry Pi 5 from an M5 Mac

Practical guide for first-time headless setup of a CanaKit Raspberry Pi 5 (SD pre-installed) from a Mac with only a Bluetooth keyboard/mouse — no HDMI monitor.

relates_to::[[raspberry-pi-5]]

---

## Core Finding: Re-flash, Don't Boot the Pre-installed SD

**CanaKit's pre-installed SD does not have SSH enabled.** Stock Raspberry Pi OS ships with SSH off for security; CanaKit does not override this. Booting the SD as-is and trying to SSH will fail. The fix is simple: the CanaKit includes a **USB card reader dongle** — use it to re-flash the SD via Raspberry Pi Imager on the Mac before first boot.

**Bluetooth keyboard/mouse cannot substitute for wired input on first boot.** Bluetooth requires OS-level pairing (a GUI or `bluetoothctl` step), which requires either a display or pre-existing network access. BT peripherals are Day 2 once the Pi is on the network.

---

## Recommended Setup Sequence

### Step 1 — Re-flash (Option A: SSH over WiFi)

1. Remove SD, insert into CanaKit USB card reader, plug into Mac
2. Download **Raspberry Pi Imager** (free, raspberrypi.com/software)
3. Select **Raspberry Pi OS 64-bit Bookworm** — NOT Trixie (the Dec 2025 Trixie image has known first-boot WiFi headless bugs)
4. Click gear/OS Customization before writing: set hostname (e.g. `mypi`), username+password, **enable SSH**, enter WiFi SSID+password, set locale
5. Write to SD, insert into Pi, power on — wait ~90 seconds
6. `ssh youruser@mypi.local` from Mac Terminal (mDNS resolves `.local` hostname automatically on same network)

### Step 2 — Add graphical access

Once SSHed in, install **Raspberry Pi Connect**:
```bash
sudo apt update && sudo apt install rpi-connect
rpi-connect on
```
Visit `connect.raspberrypi.com` in Mac browser — browser-based screen-sharing + terminal from anywhere, no VNC client required.

### Step 3 — Pair Bluetooth peripherals

Once on the network: `bluetoothctl` over SSH, or via Raspberry Pi Connect GUI → System → Bluetooth.

---

## Other Options (and why to skip them for initial setup)

| Option | Verdict |
|--------|---------|
| **USB-C gadget mode** (Pi → Mac as USB network adapter) | Trixie+ only; Pi 5 power draw can cause instability with M5 Mac USB-C PD negotiation — skip for initial setup |
| **Direct HDMI + BT** | Works if you have a spare TV/monitor; the CanaKit includes 2× microHDMI cables |
| **Edit bootfs on existing SD** (drop `ssh` empty file + `wpa_supplicant.conf`) | Works on Bookworm; simpler than full reflash if you want to preserve the pre-installed image |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `mypi.local` not resolving | `arp -a` on Mac or check router DHCP leases for Pi's IP |
| WiFi not connecting on first boot | Verify SSID/password; try 2.4 GHz band (more reliable for first connect than 5 GHz) |
| SSH connection refused | Confirm SSH was enabled in Imager; re-flash if unsure |
| Trixie WiFi issues | Use Bookworm image instead |
