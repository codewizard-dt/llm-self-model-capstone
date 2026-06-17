---
topic: "raspberry pi complete kit weight and mobile power for robot use"
slug: rpi-complete-kits
researched: 2026-06-16
---

# Primary Sources — Pi 5 Weight & Mobile Power (Addendum)

| ID | Type | Locator | Accessed | What it contributed |
|----|------|---------|----------|---------------------|
| S1 | web | https://forums.raspberrypi.com/viewtopic.php?t=361748 | 2026-06-16 | Pi 5 runs fine on 5V/3A for most use cases; USB port current limited to 600mA without 5A negotiation; "Almost all use cases will work just fine with a 3A non USB-PD supply" |
| S2 | web | https://forums.raspberrypi.com/viewtopic.php?t=366413 | 2026-06-16 | Power tool battery + buck converter approach; GPIO 5V pin method (bypasses PD); runtime and capacity discussion |
| S3 | web | https://www.reddit.com/r/raspberry_pi/comments/1ka50ng/raspberry_pi5_powerbank/ | 2026-06-16 | Standard PD banks cap at 5V/3A (PD spec); INIU bank delivers 22.5W (4.5A at 5V); 52Pi board as workaround |
| S4 | web | https://52pi.com/products/52pi-pd-power-extension-adapter-board-for-raspberry-pi-5 | 2026-06-16 | 52Pi PD Expansion Board: accepts any PD power bank, outputs 5V/8A max; resolves 5V/5A requirement without special power bank |
| S5 | web | https://www.tme.com/us/en-us/details/sc1110/raspberry-pi-minicomputers/raspberry-pi/raspberry-pi-5-2gb-ram/ | 2026-06-16 | Pi 5 gross weight (with packaging): 61.84g; bare board estimated ~46–47g |

## Excerpts

### S1 — RPi Forum: Pi 5 & Power Bank
https://forums.raspberrypi.com/viewtopic.php?t=361748
> "Almost all use cases will work just fine with a 3A non USB-PD supply... The caveat to that is that USB output current is limited to 600mA, by default."

### S3 — Reddit: Pi 5 power bank options
https://www.reddit.com/r/raspberry_pi/comments/1ka50ng/raspberry_pi5_powerbank/
> "There aren't any [5V/5A power banks]. All of the PD banks on the market support 5V but only up to 3A... I don't have the model number handy, but I have an INIU power bank I recently picked up and it supports 22.5w @ 5v - which is 4.5a."
> "Second, you could buy one of these 52Pi power boards that will draw power from any 'PD'-compatible power bank and transform it into a clean power source for the Raspberry Pi 5. In my experience, these work like a charm."

### S4 — 52Pi PD Expansion Board
https://52pi.com/products/52pi-pd-power-extension-adapter-board-for-raspberry-pi-5
> "USB-C Output: Delivers 40W power at 5V/8A MAX via a USB-C port. USB PD 3.0 Interface: Provides 5.15V@5A output through Power Delivery 3.0."

### S5 — TME.com Pi 5 product listing
https://www.tme.com/us/en-us/details/sc1110/raspberry-pi-minicomputers/raspberry-pi/raspberry-pi-5-2gb-ram/
> "Gross weight: 61.84 g"
