---
topic: "What is the current fix status of the Raspberry Pi OS Trixie WiFi headless boot bug? Is Trixie now safe for headless WiFi setup on a Raspberry Pi 5?"
slug: trixie-wifi-headless-fix
researched: 2026-06-23
---

# Primary Sources — Trixie WiFi Headless Fix Status

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://industrialmonitordirect.com/blogs/knowledgebase/raspberry-pi-zero-2w-headless-wifi-fix-trixie-vs-bookworm | 2026-06-23 | Root cause: `firstrun.sh` + Imager 1.9.4 writes WiFi country code to kernel cmdline incorrectly; Trixie's `firstrun.sh` fails to create NetworkManager profiles; workarounds and Bookworm fallback |
| S2 | web | https://github.com/raspberrypi/rpi-imager/issues/1189 | 2026-06-23 | Canonical rpi-imager bug report (CLOSED): `firstrun.sh` references `imager_custom` not present in Trixie `raspberrypi-sys-mods`; Imager 2.0.6 confirmed fix for Zero 2W |
| S3 | web | https://github.com/RPi-Distro/raspberrypi-sys-mods/issues/102 | 2026-06-23 | Root cause: `raspberrypi-sys-mods_20250630_arm64.deb` (Trixie) removed `imager_custom`; fallback writes `wpa_supplicant.conf` which NetworkManager ignores; issue is CLOSED |
| S4 | web | https://www.raspberrypi.com/news/cloud-init-on-raspberry-pi-os/ | 2026-06-23 | Official RPi announcement: cloud-init added to Trixie Nov 24 2025; Imager 2.0 required; 2.0.6+ confirmed working; writes `user-data` + `network-config` for Trixie vs `firstrun.sh` for Bookworm |
| S5 | web | https://forums.raspberrypi.com/viewtopic.php?t=395107 | 2026-06-23 | Official forum: Imager 2.0 creates cloud-init files for Trixie; rfkill keeps WiFi blocked before cloud-init runs; manual `.nmconnection` files insufficient on their own |
| S6 | web | https://hamradiohacks.substack.com/p/raspberry-pi-imager-and-trixie-11 | 2026-06-23 | Detailed account of transition break: old `imager_custom` stripped from Trixie in prep for cloud-init before cloud-init support was fully implemented; Imager 2.0.0 used on Nov 24 image |
| S7 | web | https://github.com/raspberrypi/rpi-imager/issues/1189 (comment by tosinek) | 2026-06-23 | "Zero 2 W did not work with 1.9.6 but works fine with the latest imager 2.0.6" — explicit fix confirmation for specific hardware |
| S8 | web | https://github.com/raspberrypi/rpi-imager/releases/tag/v2.0.10 | 2026-06-23 | Latest Imager release: v2.0.10, published June 19 2026; macOS `.dmg` available |
| S9 | web | https://www.raspberrypi.com/news/a-new-raspberry-pi-imager/ | 2026-06-23 | Trixie is now the officially recommended/default RPi OS; Bookworm is "Legacy" in Imager 2.0 |
| S10 | web | https://www.reddit.com/r/raspberry_pi/comments/1qafbij/updated_guide_for_raspberry_pi_zero_2w_ethernet/ | 2026-06-23 | Community confirmation: Imager 2.0.0+ required for Trixie; latest 2.0.3 at time of post; "Trixie is now the default OS so many people are going to need this updated information" |
| S11 | web | https://github.com/raspberrypi/trixie-feedback/issues/25 | 2026-06-23 | Separate WiFi disconnect bug: Pi 5 WiFi drops after 4–18 hours, does not auto-reconnect; distinct from headless first-boot issue; still open |
| S12 | web | https://github.com/raspberrypi/trixie-feedback/issues/23 | 2026-06-23 | AP compatibility issue on Zero 2W / Pi 3 with certain APs; fix: `options brcmfmac roamoff=1 feature_disable=0x82000`; does not affect Pi 5 |

---

## Excerpts

### S1 — Fixing Headless Pi Zero 2W WiFi: Trixie Bug & Bookworm Solution
https://industrialmonitordirect.com/blogs/knowledgebase/raspberry-pi-zero-2w-headless-wifi-fix-trixie-vs-bookworm
> "Affected Configuration: Raspberry Pi Imager 1.9.4 with Raspberry Pi OS Lite (Trixie) on Zero 2W. The Imager incorrectly writes the WiFi country code to the kernel command line, breaking first-boot network initialization."
> "With Trixie-based images, Imager uses a firstrun.sh mechanism via systemd: systemd.run=/boot/firstrun.sh ... This script fails to create NetworkManager profiles correctly on affected versions."
> "Version 1.9.6 may still have issues with Trixie OS specifically."

### S2 — rpi-imager issue #1189 (CLOSED)
https://github.com/raspberrypi/rpi-imager/issues/1189
> "Digging further showed that /usr/lib/raspberrypi-sys-mods/imager_custom embedded in firstboot.sh was not installed on the target image."
> (comment by tosinek): "Zero 2 W did not work with 1.9.6 but works fine with the latest imager 2.0.6"
> (comment by lurch, collaborator): "We're going to be changing the way that Raspberry Pi Imager interacts with Raspberry Pi OS Trixie, before we release our 'stable' Trixie images."

### S3 — raspberrypi-sys-mods issue #102 (CLOSED)
https://github.com/RPi-Distro/raspberrypi-sys-mods/issues/102
> "Raspberry Pi Imager v1.9.6 creates the firstrun.sh referencing /usr/lib/raspberrypi-sys-mods/imager_custom which in raspberrypi-sys-mods_20250605~bookworm_arm64.deb that file is present. However the trixie nightlies installs raspberrypi-sys-mods_20250630_arm64.deb but that file is not part of the later deb. This results in having a wpa_supplicant.conf configured that does not work with NetworkManager."

### S4 — Cloud-init on Raspberry Pi OS (official)
https://www.raspberrypi.com/news/cloud-init-on-raspberry-pi-os/
> "As some of you may have already noticed, the latest Raspberry Pi OS release based on Debian Trixie now includes cloud-init."
> "Update for anyone still struggling with this: If you're using the Trixie-based Raspberry Pi OS Lite (64-bit), make sure to use Imager v2.0.6 (or newer). The older versions like 1.8.5 won't apply your custom configuration (hostname, SSH, WiFi)."
> "It's not entirely clear to me why it fails silently with the old imager—possibly related to Trixie's switch to cloud-init for first-boot customization, which only Imager 2.x seems to understand. Either way: upgrading the Imager fixed it."
> "Trixie now includes cloud-init. This marks the beginning of a transition away from our legacy first-boot customisation system based on the firstrun.sh script."

### S6 — Ham Radio Hacks: Raspberry Pi Imager and Trixie 11-24
https://hamradiohacks.substack.com/p/raspberry-pi-imager-and-trixie-11
> "Apparently this is related to Raspberry Pi OS moving from their custom initialization system to cloud-init. During this transition, something broke in how the Imager's customization settings get processed by newer Trixie images. The old custom rpi-imager stuff was stripped out in preparation for cloud-init, but cloud-init support isn't fully implemented yet."

### S8 — rpi-imager v2.0.10 release
https://github.com/raspberrypi/rpi-imager/releases/tag/v2.0.10
> Title: v2.0.10 · Latest. Published: 2026-06-19T14:35:50Z. macOS .dmg asset: rpi-imager-v2.0.10.dmg

### S9 — A new Raspberry Pi Imager (official)
https://www.raspberrypi.com/news/a-new-raspberry-pi-imager/
> "I'm certainly able to run Imager 2.0 on labwc/Bookworm, though naturally I'd recommend Trixie as it's the supported Raspberry Pi OS release at this time."

### S11 — trixie-feedback issue #25: WiFi disconnects after some time
https://github.com/raspberrypi/trixie-feedback/issues/25
> "I have a rPI5 with the M.2 Hat+ with a rPI branded 1TB SSD (set as boot device). Device (usually) runs headless... All working fine and connection is stable for anywhere between 4 and 18 hours, at which point the rPI wifi connection drops (I cannot ping on local network or via cloudflare tunnel)."
