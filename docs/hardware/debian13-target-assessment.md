# Debian 13 Target Hardware Assessment

Date: 2026-04-16

This note captures what was confirmed through SSH/SFTP access to the target
vending PC and how the project should be prepared before replacing the current
operating system or enabling real vending hardware. Exact private network
addresses and credentials are intentionally kept out of the public repository.

## Confirmed Access

- SSH is reachable on port 22.
- SSH server banner: `SSH-2.0-9.59 FlowSsh: Bitvise SSH Server (WinSSHD) 9.59`.
- The account is restricted to Bitvise `BvShell`. It can list and read files, but
  it cannot execute normal Windows commands such as `cmd`, `powershell`, `wmic`,
  `hostname`, or `uname`.
- HTTP/HTTPS/8080 were not reachable during the check.

## Current Host

The machine is a legacy Windows-based vending PC, not a Linux controller.

Evidence:

- Root filesystem is exposed as `/C`.
- `C:\Windows`, `C:\Program Files`, `C:\ProgramData`, and `C:\Users` are present.
- There is no `C:\Program Files (x86)`, and several driver paths are `x86`, so the
  installed Windows image is very likely 32-bit.
- SetupAPI traces include `AMD ATHLON(TM) II X2 245 PROCESSOR` and ASRock/AMD
  chipset IDs.
- Page/hibernation files indicate a low-memory kiosk-class PC, likely around
  2 GB RAM. Confirm locally with the Windows inventory script before OS install.

## Hardware And Driver Clues

The current Windows install contains these vending-relevant traces:

- JCM validator tooling:
  - `C:\drivers\DBV-30x`
  - `C:\drivers\ID-003_Basic_Driver_v1.6`
  - `C:\drivers\JCM003_V2.8_(WIN)\JCM003HostSimulator.exe`
- PCI/PCIe multi-serial hardware:
  - MosChip/MCS9865: `PCI\VEN_9710&DEV_9865`
  - WCH CH38X/CH382/CH384 driver bundle under `C:\drivers\pciecom`
  - The WCH bundle includes Linux and modern Windows driver directories.
- Touchscreen:
  - GeneralTouch/SAW USB traces: `USB\VID_0DFC&PID_0001`,
    `USB\VID_0DF9&PID_0001`, and HID children.
  - Installed files under `C:\Windows\SAWtouchUSB`, `C:\Windows\SAWUsb`, and
    `C:\Windows\GenTouchScreen`.
- Connectivity:
  - Huawei mobile modem traces: `VID_12D1`.
  - `Connect Manager` and `DatacardService` folders are present.
- Possible printer or receipt hardware:
  - `C:\Program Files\Custom Engineering\CeDriver`.

The exact active COM port mapping was not confirmed because the SSH account
cannot run WMI, registry, or Device Manager commands. Run
`scripts/collect-windows-hardware-inventory.ps1` locally on the vending PC before
changing the OS.

## Project State

The repository is simulator-ready and structurally prepared for hardware, but it
is not yet a real-machine controller.

Local verification on the development machine passed:

- `python scripts\verify_project.py`
- 52 pytest tests
- UI smoke check
- simulator runtime and diagnostics smoke checks

The DBV-300-SD layer currently has a safe serial transport and a bench smoke CLI,
but the actual JCM command protocol is intentionally deferred until vendor
documentation or captured bench traces exist. Do not enable customer cash
acceptance until the DBV protocol, payout, vend motor, delivery window, pickup
sensor, and recovery behavior are bench-confirmed.

## OS Recommendation

Primary recommendation: install Debian 13 "trixie" amd64 with a minimal graphical
kiosk session.

Recommended shape:

- Debian 13 amd64 stable.
- Minimal X11 session with Openbox, LightDM autologin, and PySide6 kiosk app.
- Python virtual environment for the application.
- `systemd` service for the runtime/UI and `systemd` watchdog integration.
- Stable serial aliases through udev rules under `/dev/serial/by-id` or custom
  `/dev/flower-vending/*` symlinks.
- SSH enabled with key-based access and password login disabled after setup.
- Unattended security updates enabled.

Why Debian 13:

- It is the current Debian stable release as of this assessment.
- It is lighter and more controllable than a full desktop distribution on this
  old AMD kiosk PC.
- Linux should handle standard PCI serial, USB HID touch, and USB modem classes
  better than maintaining Windows 7.
- It fits the project's Linux paths, `systemd` model, serial transport, and
  Python/PySide6 stack.

Acceptable fallback:

- Ubuntu 24.04 LTS amd64, preferably Xubuntu/Lubuntu-style minimal desktop, if
  the team wants Canonical LTS packaging and support conventions.

Last-resort fallback:

- Windows 10 IoT Enterprise/LTSC x64 only if a Linux live boot cannot operate
  the touchscreen or serial hardware. Do not keep Windows 7 32-bit for
  production: it is obsolete, hard to secure, and a poor fit for modern
  Python/PySide6 packaging.

## Bench Plan

Before installing over the current disk:

1. Back up `C:\drivers`, `C:\Program Files\Custom Engineering`, Bitvise config,
   and any operator data.
2. Create a disk image or at least a full file backup of the current Windows
   install.
3. Run `scripts/collect-windows-hardware-inventory.ps1` locally as Administrator
   and store the output with the project artifacts.
4. Capture photos of every controller board, cable, payment device, motor driver,
   sensor board, relay board, and label.

Before committing to Debian:

1. Boot a Debian live USB without installing.
2. Run `scripts/collect-linux-hardware-inventory.sh`.
3. Confirm that PCI serial hardware appears in `lspci -nnk`.
4. Confirm serial ports under `/dev/ttyS*`, `/dev/ttyUSB*`, or
   `/dev/serial/by-id`.
5. Confirm the touchscreen appears in `/dev/input` and produces touch events.
6. Confirm display resolution, rotation, and GPU acceleration are acceptable.

After Debian install:

1. Install the app into a virtual environment.
2. Run `python scripts/verify_project.py`.
3. Validate `config/targets/machine.debian13-target.yaml`.
4. Replace the placeholder DBV serial port with the confirmed Linux device path.
5. Run DBV bench smoke only with explicit operator-provided raw bytes:
   `python -m flower_vending dbv300sd-serial-smoke --port <confirmed-port>`.
6. Store raw traces in a dedicated bench JSONL log and update the protocol tests
   before implementing production DBV commands.

## Immediate Engineering Work

- Keep simulator coverage as the release safety net.
- Add real adapters one device at a time, behind explicit configuration.
- Treat JCM/DBV command frames, denomination maps, escrow behavior, payout,
  motor movement, and pickup confirmation as bench-derived facts only.
- Add deployment scripts for the selected OS only after live-USB inventory
  confirms the hardware path.
