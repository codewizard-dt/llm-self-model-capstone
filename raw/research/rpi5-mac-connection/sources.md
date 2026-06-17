---
topic: "Options for connecting to a Raspberry Pi 5 from an M5 Mac, with a Bluetooth keyboard and mouse (CanaKit Starter Kit, SD pre-installed)"
slug: rpi5-mac-connection
researched: 2026-06-17
---

# Primary Sources — RPi 5 Mac Connection Options

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://www.canakit.com/canakit-raspberry-pi-5-starter-kit-turbine-black.html | 2026-06-17 | Kit contents: 128GB SD pre-loaded with 64-bit Pi OS, USB card reader dongle, 2× microHDMI cables, USB-C PD power supply |
| S2 | web | https://www.reddit.com/r/raspberry_pi/comments/1jodbbc/help_with_canakit_raspberry_pi_5_desktop_pc_with/ | 2026-06-17 | CanaKit does not pre-enable SSH; community recommends keyboard + screen for initial setup or re-imaging SD |
| S3 | web | https://www.raspberrypi.com/news/usb-gadget-mode-in-raspberry-pi-os-ssh-over-usb/ | 2026-06-17 | Trixie images (20 Oct 2025+) ship with rpi-usb-gadget package; single toggle in Pi Imager enables USB ethernet gadget mode; SSH via hostname without WiFi/Ethernet |
| S4 | web | https://forums.raspberrypi.com/viewtopic.php?t=392845 | 2026-06-17 | Pi 5 USB-C gadget mode + Mac issues: "Pi 5 takes more power so it is less likely to work well being powered from the USB C bus on the Macintosh" |
| S5 | web | https://devguide.dev/blog/raspberry-pi-headless-ssh-setup | 2026-06-17 | Trixie (Dec 2025) has WiFi connectivity issues on first headless boot; Bookworm is more reliable for headless WiFi |
| S6 | web | https://www.raspberrypi.com/software/connect/ | 2026-06-17 | Raspberry Pi Connect: free browser-based remote access (desktop + terminal) for Pi 4/5 running 64-bit Bookworm with Wayland |
| S7 | web | https://www.tomshardware.com/reviews/raspberry-pi-headless-setup-how-to,6028.html | 2026-06-17 | Bookworm headless setup flow: Pi Imager → OS Customization → enable SSH + WiFi; for VNC on Bookworm use TigerVNC |

## Excerpts

### S2 — CanaKit SSH status (Reddit)
https://www.reddit.com/r/raspberry_pi/comments/1jodbbc/help_with_canakit_raspberry_pi_5_desktop_pc_with/
> "The simplest thing is to get a keyboard and screen for the initial setup."
> "Other than imaging an SD card and booting from that, I don't see how you can do it, since the Canakit boots from the SSD and does not have [SSH pre-enabled]."

### S3 — Trixie USB gadget mode (official Raspberry Pi)
https://www.raspberrypi.com/news/usb-gadget-mode-in-raspberry-pi-os-ssh-over-usb/
> "Starting with Raspberry Pi OS Trixie images dated 20.10.2025 and later, a new package called rpi-usb-gadget is included by default. It can be enabled with a single toggle in Raspberry Pi Imager, making USB networking setup drastically simpler. You can SSH directly using the hostname you set in Raspberry Pi Imager — no Wi-Fi or Ethernet setup required."

### S4 — Pi 5 USB-C gadget + Mac power issues (RPi Forums)
https://forums.raspberrypi.com/viewtopic.php?t=392845
> "The Pi 5 takes more power so it is less likely to work well being powered from the USB C bus on the Macintosh."
> "Might be on the Mac end. When you power via GPIO and connect to a USB host via the Pi's USB C port power may flow in the wrong direction. Which may confuse PD on the Mac."

### S5 — Trixie WiFi headless issue
https://devguide.dev/blog/raspberry-pi-headless-ssh-setup
> "As of December 2025, the newest Raspberry Pi OS images are based on Debian Trixie. These have WiFi connectivity issues that prevent headless setup from working - the Pi will not connect to WiFi on first boot."

### S6 — Raspberry Pi Connect official
https://www.raspberrypi.com/software/connect/
> "Raspberry Pi Connect gives you free, simple, out-of-the-box access to your Raspberry Pi from anywhere in the world. It is a secure remote access solution for Raspberry Pi OS, allowing you to connect to your Raspberry Pi desktop and command line directly from any browser."
