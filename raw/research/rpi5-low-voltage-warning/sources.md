---
topic: "Is there any real advantage to addressing the Pi 5 'low voltage' warning, and is the 52Pi PD Expansion Board the only way to fix it?"
slug: rpi5-low-voltage-warning
researched: 2026-06-17
---

# Primary Sources — Raspberry Pi 5 Low Voltage Warning

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://forums.raspberrypi.com/viewtopic.php?t=373841 | 2026-06-17 | Confirmed 600 mA USB cap when no 5A PD negotiated; 1.6A when 5A supply confirmed; `PSU_MAX_CURRENT=5000` config.txt workaround |
| S2 | web | https://forums.raspberrypi.com/viewtopic.php?t=361206 | 2026-06-17 | `usb_max_current_enable=1` in `/boot/firmware/config.txt` forces full USB current and enables USB boot on 3A supply |
| S3 | web | https://news.sparkfun.com/8391 | 2026-06-17 | Official SparkFun coverage: "total power drawn from the four USB ports on Raspberry Pi 5 is limited by default to a nominal 600mA; this limit is automatically increased to a nominal 1.6A when the USB-C PD Power Supply is detected" |
| S4 | web | https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-009856-WP-1-USB%20Power%20delivery%20on%20Raspberry%20Pi%205.pdf | 2026-06-17 | Official RPi white paper: "Raspberry Pi 5 will request a 5V 5A supply via the USB PD system, but will revert to 3A if no 5A PDO is present." Available PDOs: 5V/3A, 5V/5A, 9V/5A, 12V/3.75A, 15V/3A, 20V/2.25A. |
| S5 | web | https://forums.raspberrypi.com/viewtopic.php?t=357130 | 2026-06-17 | "5V 5A is simply not allowed in the [USB PD] specification" — Pi 5's preferred profile is out-of-spec; virtually no commodity charger implements it |
| S6 | web | https://www.reddit.com/r/raspberry_pi/comments/1abwpof/disabling_power_delivery_on_raspberry_pi_5/ | 2026-06-17 | Community confirmation: `PSU_MAX_CURRENT=5000` DOES unlock full USB peripheral current; the on-screen warning may still flash but USB works at full 1.6A |
| S7 | web | https://bret.dk/how-to-power-the-raspberry-pi-5-a-complete-guide/ | 2026-06-17 | Complete power guide: "Most standard USB-PD chargers offer 5V/3A (15W) as their base profile. The Raspberry Pi 5 specifically looks for a 5.1V/5A profile to unlock its full potential. If the Pi doesn't detect this 5A supply at boot, it automatically limits the USB port current to 600mA." |
| S8 | web | https://52pi.com/products/52pi-pd-power-extension-adapter-board-for-raspberry-pi-5 (via thepihut.com) | 2026-06-17 | 52Pi PD Expansion Board: negotiates higher-voltage PD (9–24V DC input also accepted), steps down to 5V/5A for Pi 5; ~£23 |
| S9 | web | https://pichondria.com/2024/08/06/power-rpi5-using-powerbank/ | 2026-06-17 | Alternative to 52Pi: Pichondria board negotiates any PD bank and converts to 5V/5A for Pi 5 |
| S10 | web | https://www.reddit.com/r/raspberry_pi/comments/1q4mctl/powering_a_raspberry_pi_5_from_a_usbc_pd/ | 2026-06-17 | DIY path: PD trigger (fixed 9V) + buck converter (9V→5V/8A) wired directly to Pi 5; confirmed working; ~$8–15 in parts |

---

## Excerpts

### S1 — RPi Forum: RPi5 Low Voltage Warning
https://forums.raspberrypi.com/viewtopic.php?t=373841
> "In order to avoid demanding more than 3A, the Pi5 will limit its USB source to 600mA. If it is told that it has a 5A capable supply, it will increase its USB source limit to 1A6. The higher limit is selected by a PD-negotiated 5V 5A mode, or by manual configuration."
> "The work around to this was to editing config.txt to have ... PSU_MAX_CURRENT=5000."

### S3 — SparkFun: Meet the Raspberry Pi 5
https://news.sparkfun.com/8391
> "The total power drawn from the four USB ports on Raspberry Pi 5 is limited by default to a nominal 600mA; this limit is automatically increased to a nominal 1.6A when the USB-C PD Power Supply is detected."

### S4 — Official Raspberry Pi USB PD White Paper
https://pip-assets.raspberrypi.com/categories/685-app-notes-guides-whitepapers/documents/RP-009856-WP-1-USB%20Power%20delivery%20on%20Raspberry%20Pi%205.pdf
> "Raspberry Pi 5 will request a 5V 5A supply via the USB PD system, but will revert to 3A if no 5A PDO is present."
> "While Raspberry Pi recommends a 5V 5A supply for Raspberry Pi 5, it will function perfectly well with a 3A supply, provided that only lower-power peripherals are attached."

### S5 — RPi Forum: Raspberry Pi5 USB-C PD
https://forums.raspberrypi.com/viewtopic.php?t=357130
> "5V 5A is simply not allowed in the specification [USB PD fixed-voltage charging model]. The choice to use an out-of-spec power profile will limit the use of Pi5 with basically all compliant chargers already on the market."
> "I have still yet to come across any 5V 5A capable chargers in the wild (besides the Pi one) regardless of the PDO."

### S7 — bret.dk: How to Power the Raspberry Pi 5
https://bret.dk/how-to-power-the-raspberry-pi-5-a-complete-guide/
> "Most standard USB-PD chargers offer 5V/3A (15W) as their base profile. The Raspberry Pi 5 specifically looks for a 5.1V/5A profile to unlock its full potential. If the Pi doesn't detect this 5A supply at boot, it automatically limits the USB port current to 600mA. This is why your SSDs or high-power peripherals might fail to mount even if you are using a 'high wattage' charger."
