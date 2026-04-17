# Hardware Bench Validation Checklist

Date: 2026-04-17

This checklist turns the current simulator-first baseline into a bench-ready
hardware validation plan. It is intentionally evidence-gated: do not implement
or enable real vending behavior until the required bench artifacts exist.

Sources:

- `docs/hardware/dbv300sd-bench-plan.md`
- `docs/hardware/debian13-target-assessment.md`
- `config/targets/machine.debian13-target.yaml`

## Scope And Rule

The Debian 13 target config is a starting point, not a production config. Every
device marked `requires_hardware_confirmation: true`, every placeholder path
such as `/dev/serial/by-id/REQUIRES_HARDWARE_CONFIRMATION`, and every
`requires_hardware_confirmation` driver must be replaced only with bench facts.

Use this checklist to collect those facts. Keep captures, photos, inventory
outputs, serial traces, service logs, and operator notes as release artifacts or
private bench artifacts. Do not put credentials, private IPs, or customer data
in git.

## Evidence Package Required For Bench Ready

- Windows pre-migration inventory from
  `scripts/collect-windows-hardware-inventory.ps1`.
- Linux live-USB inventory from `scripts/collect-linux-hardware-inventory.sh`.
- Photos of controller boards, labels, cable routing, payment hardware, payout
  device, motor driver, sensors, relay boards, touchscreen, modem, and power
  wiring.
- Stable Linux device paths for every serial/input device.
- Timestamped DBV raw rx/tx JSONL traces from
  `python -m flower_vending dbv300sd-serial-smoke`.
- Payout, motor, window, sensor, watchdog, kiosk, service/autostart, and recovery
  test records with expected action, observed physical result, timestamp,
  operator, and pass/fail.
- A signed bench summary that names every config value changed from the target
  template and links it to captured evidence.

## Phase 0 - Safety And Setup

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| Current Windows install backed up before OS replacement | Disk image or full file backup manifest | Recovery path exists before Debian install | None |
| Driver folders backed up | Archive containing `C:\drivers`, Custom Engineering files, Bitvise config if needed | JCM/serial/touch/printer clues preserved | None |
| Cabinet power and emergency stop procedure documented | Photo and operator note | Bench operator can cut power safely | None |
| Cash handling area controlled | Operator note | Test bills/coins tracked and reconciled | None |
| Bench artifact directory created | Artifact path and naming convention | Logs/traces/photos are easy to audit | None |

## Phase 1 - Debian 13 Hardware Inventory

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| Debian live USB boots without installing | Photo or boot log | Display and keyboard/touch access available | Confirms Debian path is viable |
| PCI serial hardware detected | `lspci -nnk` from Linux inventory | MosChip/WCH serial adapters visible with drivers | Enables serial mapping work |
| Serial devices enumerated | `/dev/ttyS*`, `/dev/ttyUSB*`, `/dev/serial/by-id` listing | Stable target candidate exists for DBV and other serial devices | Replace DBV placeholder port only after DBV-specific test |
| Touchscreen emits input events | `libinput list-devices` or event capture | Touch maps to kiosk display accurately | Kiosk readiness input |
| Display resolution and rotation confirmed | Screenshot/photo and `xrandr` output | UI is readable and correctly oriented | Kiosk config notes |
| Network path confirmed | SSH and update logs | Remote support and package install path available | Deployment docs only |

## Phase 2 - DBV-300-SD Validator

Do not add protocol bytes from memory or guesses. Follow
`docs/hardware/dbv300sd-bench-plan.md`.

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| Physical protocol mode identified | Vendor docs, board photo, cabling photo, or bench note | Serial/MDB/pulse/bridge mode is known | Confirms `transport_kind` and `protocol_kind` |
| Serial settings confirmed | Raw trace metadata and operator note | Baudrate, byte size, parity, stop bits, timeouts, flow control known | Update `devices.bill_validator.serial` |
| Stable Linux port confirmed | `/dev/serial/by-id` or udev symlink evidence | Port survives unplug/replug and reboot | Replace DBV serial port placeholder |
| Startup disabled state confirmed | Raw rx/tx trace | Validator reaches safe disabled idle state after startup | Confirms startup behavior |
| Enable/disable acceptance confirmed | Raw rx/tx trace and physical observation | Acceptance can be enabled and disabled, including idle disable | Enables acceptance control implementation |
| Polling or push model confirmed | Raw trace across idle and bill insert | No-data, bill-in-progress, accepted, rejected, fault events identified | Event loop design evidence |
| Denomination map confirmed | One trace per accepted bill denomination | Every supported bill maps to the configured minor units | Confirms `accepted_denominations_minor` |
| Escrow behavior confirmed or ruled out | Raw trace and vendor/bench note | Stack/return semantics are known, or explicitly unsupported | Payment/recovery design evidence |
| Jam/cassette/disabled faults captured | Raw trace plus physical action note | Fault codes and recovery requirements are known | Fault mapping evidence |
| Power-cycle and transport-loss recovery captured | Raw trace and restart log | Ambiguous bill-in-path behavior is understood | Recovery requirements |

Gate to implement real DBV protocol:

- Every command byte and event mapping used by the implementation is backed by
  vendor documentation or bench traces.
- Tests exist for confirmed frames using fake transport.
- Simulator remains the default unless deployment config explicitly selects the
  confirmed implementation.

## Phase 3 - Payout Hardware

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| Device model and protocol identified | Photo, manual, wiring, transport path | Payout protocol and denomination channels known | Replace `change_dispenser.driver` placeholder |
| Channel-to-denomination map confirmed | Dispense trace and cash count | Every configured denomination maps to the correct payout channel | Update `change_inventory` assumptions |
| Inventory read/reconcile behavior confirmed | Device status log and manual cash count | Software count can be reconciled with physical state | Enables reconciliation workflow |
| Exact payout success path tested | Command trace, cash count, transaction note | Requested change is dispensed exactly | Confirms payout command behavior |
| Insufficient change path tested | Command trace and UI/operator observation | System blocks unsafe sale or enters exact-change-only | Policy evidence |
| Partial payout/ambiguous result tested safely | Trace, cash count, manual review note | Recovery marks transaction ambiguous/manual review | Recovery evidence |
| Jam/empty/cassette fault captured | Trace and physical action note | Fault mapping and operator action are known | Fault mapping evidence |

Gate to implement payout adapter:

- Payout commands, status reads, channel maps, timeouts, retry rules, and
  ambiguous-result handling are bench-confirmed.

## Phase 4 - Vend Motors, Position, And Delivery Window

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| Motor controller model and transport identified | Photo/manual/wiring | Driver path is known | Replace `motor_controller.driver` placeholder |
| Slot-to-motor mapping confirmed | Test vend per slot with photo/video | Correct physical slot actuates for every configured slot | Update `mapping` and catalog/slot config |
| Home/position sensor behavior confirmed | Trace/log/photo | Controller can establish safe known position | Replace `position_sensor.driver` placeholder |
| Normal vend timing measured | Timestamped run log | Timeout values are based on real movement time | Update `timeouts_ms.vend/home` |
| Stall/fault/timeout tested safely | Trace and operator note | Faults do not continue motor movement unsafely | Fault mapping and retry evidence |
| Delivery window open/close tested | Trace/video/operator note | Window reaches open and closed states reliably | Replace `window_controller.driver` placeholder |
| Window obstruction/ambiguous close tested | Trace/video/operator note | System enters manual review or safe blocked state | Recovery evidence |

Gate to implement motor/window adapters:

- Movement commands, position confirmation, stop behavior, timeouts, and physical
  fault states are measured and mapped.

## Phase 5 - Sensors And Cooling

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| Service door sensor polarity confirmed | Open/close readings with photos | Open and closed states map correctly | Replace `door_sensor.driver` placeholder |
| Inventory sensor presence behavior confirmed | Empty/loaded slot readings | Presence and confidence values are meaningful | Replace `inventory_sensor.driver` placeholder |
| Position sensor calibration confirmed | Known positions and readings | Position state is repeatable after reboot | Replace `position_sensor.driver` placeholder |
| Temperature sensor calibrated | Reference thermometer comparison | Readings are within accepted tolerance | Replace `temperature_sensor.driver` placeholder |
| Critical temperature threshold tested | Controlled test or simulated hardware input | System blocks sale and logs critical condition | Confirms `critical_temperature_celsius` |
| Cooling relay/control path confirmed | Command log and physical observation | Cooling command affects the expected hardware | Replace `cooling_controller.driver` placeholder |
| Sensor disconnect/fault behavior captured | Trace/operator note | Faults produce safe sale blockers | Fault mapping evidence |

Gate to implement sensor/cooling adapters:

- Polarity, units, thresholds, sampling rates, disconnection behavior, and
  calibration method are documented with bench evidence.

## Phase 6 - Watchdog, Service, And Autostart

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| systemd unit drafted but not enabled for production | Unit file in bench artifact | Starts app with correct user/env/working dir | Confirms `autostart_mode: systemd` design |
| App starts after boot | `journalctl` and timestamped boot test | Runtime/UI starts without manual shell command | Service readiness |
| Graceful stop/restart tested | `systemctl stop/restart` logs | SQLite closes cleanly, no corruption | Service readiness |
| Crash restart tested | Forced process failure and `journalctl` | Service restarts within expected window | Restart policy evidence |
| systemd watchdog heartbeat confirmed | `WatchdogSec` config and logs | Missed heartbeat triggers restart | Replace watchdog adapter placeholder only if implemented |
| Power-loss restart tested | Power-cycle note and logs | Machine returns to safe state and recovery summary is readable | Recovery readiness |
| Log rotation and permissions confirmed | File listing and rotated logs | `/var/log/flower-vending` writable and bounded | Logging config evidence |
| SQLite path permissions confirmed | File listing and write test | `/var/lib/flower-vending/flower_vending.db` writable by service user | Persistence config evidence |

Gate to enable autostart/watchdog:

- Boot, restart, crash, watchdog, log, and SQLite permission tests pass on the
  target cabinet.

## Phase 7 - Kiosk Lockdown

| Check | Evidence | Pass Criteria | Config Impact |
| --- | --- | --- | --- |
| Dedicated kiosk user created | User/group listing | App runs without admin/root privileges | Deployment docs |
| Autologin kiosk session configured | LightDM/session config artifact | UI appears after boot without shell exposure | Kiosk readiness |
| Fullscreen and display geometry confirmed | Photo/screenshot | UI fills display with correct rotation/scaling | Confirms `ui.kiosk_fullscreen` |
| Keyboard shortcuts and shell escape blocked | Operator test note | User cannot leave app through common shortcuts | Lockdown evidence |
| Touch calibration persists after reboot | Touch test and config artifact | Touch remains aligned | Kiosk readiness |
| Remote support path preserved | SSH config note | Maintainers can access without exposing customer UI | Operations readiness |

Gate to call kiosk ready:

- UI starts after boot, touch works, shell escape paths are closed, and remote
  support remains available.

## Phase 8 - End-To-End Recovery Validation

| Scenario | Evidence | Pass Criteria |
| --- | --- | --- |
| Clean startup with no unresolved state | `status --json`, events, service log | Machine reaches idle/safe-ready state |
| Restart during payment before bill acceptance | Trace and `status --json` | No cash liability is created |
| Restart with bill in path or ambiguous DBV event | DBV trace, journal, operator note | System blocks sale and requires manual review |
| Payout partial/failed after accepted payment | Payout trace, cash count, journal | Transaction enters recovery/manual review with correct liability |
| Product vend failure | Motor trace, journal, UI/operator note | Sale is blocked or recovery path is explicit |
| Window open but pickup not confirmed | Sensor/window trace and journal | Pickup timeout/manual review behavior matches policy |
| Service door opens mid-flow | Sensor trace and journal | Sale is blocked and operator status explains why |
| Critical temperature during idle and active sale | Sensor trace and journal | Sale blockers and recovery behavior match policy |
| Power loss during active transaction | Boot logs, SQLite state, `events --limit N` | Restart restores unresolved state without unsafe commands |

Gate to pilot:

- Every recovery scenario has a reproducible bench record.
- `python -m flower_vending status --json` gives an operator-readable recovery
  summary after each restart/failure.
- `python -m flower_vending events --limit N --json` shows the event trail needed
  to explain the state.

## Config Promotion Rules

Only promote `config/targets/machine.debian13-target.yaml` toward production
after all relevant evidence exists:

- Replace placeholder `driver: requires_hardware_confirmation` only with a named
  adapter backed by bench tests.
- Replace `/dev/serial/by-id/REQUIRES_HARDWARE_CONFIRMATION` only with a stable
  confirmed device path or udev symlink.
- Adjust timeouts only from measured timings.
- Adjust denomination, slot, sensor, and relay mappings only from physical tests.
- Keep `simulator.enabled: false` for the hardware target, but keep simulator
  configs as the release safety net.
- Document every promoted value in a bench summary before using it in pilot.

## Exit Criteria

The project is Bench Ready when:

- Simulator verification still passes.
- Debian target config validates with only intentionally unresolved future
  warnings removed or explained.
- Every real adapter selected by config has bench evidence and tests.
- Service/autostart/watchdog/kiosk paths pass reboot and crash tests.
- Recovery paths are proven with SQLite state, journal events, operator status,
  and physical cash/product reconciliation.

The project is not Pilot Ready until real cash acceptance, payout liability,
vend movement, delivery window safety, sensor faults, and power-loss recovery
are all bench-confirmed on the actual cabinet.
