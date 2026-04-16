#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_OUTPUT_DIR="${SCRIPT_DIR}/../artifacts/hardware-inventory-linux"
OUTPUT_DIR="${1:-$DEFAULT_OUTPUT_DIR}"

mkdir -p "$OUTPUT_DIR"

run_capture() {
  local name="$1"
  shift
  {
    echo "\$ $*"
    "$@"
  } >"${OUTPUT_DIR}/${name}.txt" 2>&1 || true
}

run_shell_capture() {
  local name="$1"
  local command="$2"
  {
    echo "\$ ${command}"
    sh -c "$command"
  } >"${OUTPUT_DIR}/${name}.txt" 2>&1 || true
}

{
  echo "CollectedAt=$(date -Is)"
  echo "Hostname=$(hostname 2>/dev/null || true)"
  echo "Kernel=$(uname -a 2>/dev/null || true)"
  if [ -r /etc/os-release ]; then
    cat /etc/os-release
  fi
} >"${OUTPUT_DIR}/system-summary.txt" 2>&1

run_capture lscpu lscpu
run_capture memory free -h
run_capture block-devices lsblk -o NAME,PATH,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,SERIAL
run_capture pci lspci -nnk
run_capture usb lsusb
run_capture usb-tree lsusb -tv
run_capture serial-devices sh -c 'ls -l /dev/ttyS* /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/* /dev/serial/by-path/* 2>/dev/null'
run_capture input-devices sh -c 'ls -l /dev/input/by-id/* /dev/input/by-path/* 2>/dev/null; cat /proc/bus/input/devices 2>/dev/null'
run_capture libinput sh -c 'command -v libinput >/dev/null 2>&1 && libinput list-devices'
run_capture udev-serial sh -c 'for d in /dev/ttyS* /dev/ttyUSB* /dev/ttyACM*; do [ -e "$d" ] && udevadm info --query=all --name="$d"; done'
run_capture udev-input sh -c 'for d in /dev/input/event*; do [ -e "$d" ] && udevadm info --query=all --name="$d"; done'
run_capture network ip addr
run_capture routes ip route
run_capture systemd systemctl --type=service --state=running --no-pager
run_capture python python3 --version
run_capture pip sh -c 'python3 -m pip --version'
run_shell_capture dmesg-relevant 'dmesg | grep -Ei "tty|serial|usb|input|touch|hid|moschip|mcs|wch|ch38|jcm|dbv|printer|modem"'

echo "Hardware inventory written to ${OUTPUT_DIR}"
