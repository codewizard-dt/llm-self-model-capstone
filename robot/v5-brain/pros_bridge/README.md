# Brain Bridge Notes

This is a starter sketch for the V5 Brain side. It is intentionally conservative because the Brain is not physically here yet.

The Pi side is ready to speak newline-delimited JSON over the V5 USB user/console serial port. Tomorrow we need to verify the exact PROS stream setup on the physical Brain.

Useful confirmed references:

- VEX exposes a second console serial port over USB for V5 Brain console/user output.
- PROS can interact with serial streams through file-style `stdin`, `stdout`, and related stream identifiers.
- PROS documents `SERCTL_DISABLE_COBS`; use it when reading serial yourself instead of using `pros terminal`.

