#!/usr/bin/env bash
set -euo pipefail

echo "USB devices:"
lsusb || true
echo
echo "Serial devices:"
ls -la /dev/ttyACM* /dev/ttyUSB* /dev/serial/by-id/* 2>/dev/null || true
echo
echo "Kernel messages mentioning tty/usb/vex:"
dmesg | grep -Ei "ttyACM|ttyUSB|VEX|Innovation|cdc_acm|usb" | tail -n 80 || true

