# Full Hardware Replacement Plan

Date: 2026-04-23

This document is the "stop trying to reverse-engineer the old cabinet" plan for
the flower vending machine. The goal is to replace the unknown ATmega relay
board and undocumented wiring with a maintainable cabinet architecture that can
be driven by `flower-vending-system`.

The plan assumes:

- the old PC/control board context is unreliable or lost;
- the existing cabinet, screen, DBV bill validator, printer, motors, window,
  cooling and power hardware may be reused only after bench tests;
- the old ATmega32A relay board is not trusted as a production controller;
- the software repository is a target baseline, not proof of the old wiring.

## Recommended Direction

Use a normal PC for the kiosk UI and vending application, and use DIN-rail
industrial I/O modules for motors, sensors, window and cooling:

```text
PC running flower-vending-system
  |-- USB/RS-232 or PCIe COM card --> JCM DBV-300-SD bill validator
  |-- USB                         --> Custom VKP80 receipt printer
  |-- USB/RS-485 isolated adapter --> Modbus RTU I/O modules
                                      |-- relay outputs
                                      |-- dry-contact inputs
                                      |-- temperature module
```

Recommended control stack:

1. PC with Windows 10/11 or Debian Linux.
2. Isolated USB-to-RS485 adapter.
3. Two Wiren Board `WB-MR6C v.3` relay/input modules.
4. One Wiren Board `WB-M1W2` 1-Wire temperature module, or an equivalent
   Modbus temperature module.
5. 24 VDC control power, DIN-rail fuses, terminals, E-stop and contactors.

Why this route:

- no custom microcontroller firmware is needed for basic I/O;
- Modbus RTU is easy to test from a PC and from Python;
- relay modules have terminals, status LEDs and documented registers;
- inputs and outputs can be mapped explicitly in YAML config;
- the old unknown relay board can be removed from the critical path.

## Architectures Compared

| Option | Use when | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- |
| PC + Wiren Board Modbus I/O | You want maintainable replacement with reasonable cost | DIN rail, documented, Modbus, no firmware | More expensive than Arduino | Best default |
| PC + OVEN PR205/Mx110/Mx210 | You want Russian industrial PLC ecosystem | Industrial, Modbus TCP/RTU, good support | Need PLC logic or more Modbus work | Good industrial alternative |
| PC + CONTROLLINO | You want Arduino-like but more industrial | Arduino-compatible, 12/24 V automation I/O | Less common locally, more expensive | Good if available |
| PC + Arduino Mega + relay boards | Lowest cost bench prototype | Cheap, many GPIO | Needs firmware, fragile wiring, weak safety unless built carefully | Bench only unless rebuilt professionally |
| PC + Numato/Advantech USB relay module | Very quick USB relay control | Appears as COM/USB, no controller firmware | Inputs/sensors still separate, not ideal for cabinet-wide I/O | Useful for lab/testing |

## Shopping List: Recommended Build

Prices and availability change. Treat the links as product references and buy
from a supplier that can deliver genuine parts to your location.

### Core PC And Communications

| Qty | Item | Recommended examples | Notes |
| ---: | --- | --- | --- |
| 1 | PC or mini-PC | Any reliable Windows 10/11 or Debian-capable PC, 8 GB RAM, SSD 256 GB+ | Reuse existing PC if stable; otherwise use a fanless industrial mini-PC if budget allows. Advantech has fanless embedded PCs with COM options. |
| 1 | RS-232 ports for DBV/payout | Existing WCH PCIe CH384 card or FTDI/Moxa USB-RS232 adapters | WCH CH384 is a PCIe quad UART chip; keep it if it works. |
| 1 | Isolated USB-RS485 adapter | Waveshare industrial isolated USB-RS485/422, or Moxa UPort 1130I | Used for Modbus RTU I/O modules. Isolation is strongly preferred. |
| 1 | Powered USB hub, industrial if possible | Any good powered hub | Useful for printer, RS485, RS232, service keyboard. |

Links:

- WCH CH384 product page: https://www.wch-ic.com/products/CH384.html
- WCH CH38X driver page: https://www.wch-ic.com/downloads/CH38XDRV_ZIP.html
- Waveshare isolated USB-RS485/422: https://www.waveshare.com/usb-to-rs485-422.htm
- Moxa UPort 1130I isolated RS-422/485 adapter: https://www.moxa.com/en/products/industrial-edge-connectivity/usb-to-serial-converters-usb-hubs/usb-to-serial-converters/uport-1100-series/uport-1130i
- Advantech fanless embedded PCs: https://buy.advantech.com/embedded-series/compact-embedded-computers/dhtml-1614.htm

### Modbus I/O

| Qty | Item | Recommended examples | Purpose |
| ---: | --- | --- | --- |
| 2 | Relay + input module | Wiren Board `WB-MR6C v.3` | 12 relay outputs and 14 dry-contact inputs total. |
| 1 | 1-Wire temperature module | Wiren Board `WB-M1W2` | Read DS18B20 chamber/evaporator sensors over Modbus. |
| 2-3 | DS18B20 waterproof probes | Genuine Maxim/Analog Devices or decent probe assemblies | Chamber temperature, evaporator temperature, optional ambient. |
| optional | Extra input module | OVEN `MV110` / `MV210`, or another `WB-MR6C` | Add more slot sensors if needed. |
| optional | Extra output module | OVEN `MU110` / `MU210`, or another `WB-MR6C` | Add more motors/lamps/locks. |

Links:

- Wiren Board `WB-MR6C v.3`: https://wirenboard.com/ru/product/WB-MR6C_v3/
- `WB-MR6C v.3` manual/wiki: https://wiki.wirenboard.com/wiki/WB-MR6C_v.3_Modbus_Relay_Modules
- Wiren Board `WB-M1W2` 1-Wire temperature module: https://wiki.wirenboard.com/wiki/index.php?title=WB-M1W2_1-Wire_to_Modbus_Temperature_Measurement_Module/en
- DS18B20 datasheet reference: https://www.digikey.com/htmldatasheets/production/1668/0/0/1/ds18b20z-t-r.html
- OVEN PR205: https://owen.ru/product/pr205
- OVEN MV110 input modules: https://owen.ru/product/moduli_diskretnogo_vvoda_s_interfejsom_rs_485
- OVEN MU110 output modules: https://owen.ru/product/moduli_diskretnogo_vivoda_s_interfejsom_rs_485
- OVEN MU210 Ethernet output modules: https://owen.ru/product/moduli_diskretnogo_vivoda_ethernet

### Power And Cabinet Parts

| Qty | Item | Recommended examples | Notes |
| ---: | --- | --- | --- |
| 1 | 24 VDC DIN power supply | Mean Well `HDR-60-24` or larger | Main control voltage for relays/sensors/contactors. |
| 1 | 5 VDC DIN power supply | Mean Well `HDR-15-5` | Only if using 5 V logic, USB relay boards or LEDs. |
| 1 | 12 VDC supply | 12 V, 3-5 A | For DBV-300-SD if the old 12 V supply is not reused. |
| 1 | 24 VDC supply for printer | 24 V, at least printer-rated current | Custom VKP80 family is typically 24 VDC. Confirm exact model label. |
| many | DIN rail terminal blocks | WAGO/Phoenix/IEK/etc. | Separate PE, N, L, 24V, 0V, sensor commons. |
| many | Fuse terminals / DC breakers | Per output group | Every motor/actuator branch gets protection. |
| 1 | RCD/RCBO and MCBs | Eaton/ABB/Schneider/etc. | Must be selected by an electrician for local mains. |
| 1 | PE/ground bar | Any proper cabinet bar | Cabinet, door, PC chassis, power supplies and shield drains need PE. |
| 1 | Wire duct, ferrules, labels | Any cabinet wiring kit | Do not build the new panel without labels. |

Links:

- Mean Well `HDR-60-24` Russia store reference: https://www.mean-well.ru/store/HDR-60-24/
- Mean Well `HDR-15` series: https://www.meanwell.co.uk/power-supplies/din-rail-power-supplies/hdr-15-series
- Mean Well HDR DIN rail installation manual: https://www.meanwell.com/Upload/PDF/HDR-15/HDR%20DIN%20rail%20power%20supply.pdf

### Safety And 220 V Switching

| Qty | Item | Recommended examples | Purpose |
| ---: | --- | --- | --- |
| 1 | Emergency stop mushroom button | Schneider Harmony XB4/XB5 or equivalent | Human emergency stop input. |
| 1 | Safety relay | Pilz PNOZ X/PNOZsigma or equivalent | E-stop should cut actuator power through safety contacts. |
| 1+ | Contactors | Schneider/ABB/IEK contactors with correct coil voltage | Compressor, motor mains, grouped actuator power. |
| many | RC snubbers / varistors | Match coil/load voltage | Protect relay contacts from inductive loads. |
| many | Flyback diodes | For DC coils/solenoids | Across DC inductive loads, polarity correct. |

Links:

- Pilz PNOZ X safety relays: https://www.pilz.com/en-US/products/relay-modules/safety-relays-protection-relays/pnoz-x-safety-relays/0010000200700280fn/index.html
- Pilz safety relay overview: https://www.pilz.com/en-US/products/relay-modules/safety-relays-protection-relays
- Schneider Harmony emergency stop example: https://www.se.com/ww/products/US/en/products/ZB4BS844
- Eaton RCBO example: https://www.eaton.com/us/en-us/skuPage.EAD32BH30C-A.html

### Payment And Receipt Hardware

| Device | Recommended approach | Notes |
| --- | --- | --- |
| Bill validator | Keep existing JCM DBV-300-SD if it passes bench tests | Connect to PC over RS-232. Do not invent protocol frames. |
| Printer | Keep existing Custom VKP80 if it prints reliably | Prefer USB. Confirm 24 V power and exact model label. |
| Payout/change | Replace with a documented MDB changer/payout plus MDB-USB/MDB-RS232 interface, or remove cash change from MVP | Payout is the riskiest part of cash vending. |
| Cashless | Prefer professional unattended terminal if business rules allow it | Nayax/Vendotek type systems use MDB/Pulse/etc. Contract/support matters. |

Links:

- JCM DBV-30X manual reference: https://www.vend-resource.com/sites/default/files/JCM-OptiPay-DBV-30X-Series-Manual.pdf
- Custom VKP80II RX official page: https://www.custom.biz/en_US/product/hardware/professional-printing-solutions/kiosk-receipt-printers/vkp80ii-sx
- Qibixx MDB-USB interface: https://qibixx.com/mdb-usb-interface/
- Qibixx MDB technology overview: https://mdb.technology/
- Nayax VPOS Touch: https://www.nayax.com/solution/vpos-touch/
- Vendotek cashless payments: https://www.vendotek.eu/

### Cooling

Do not make the PC or Python app the only thing protecting flowers from a bad
temperature condition. Cooling should have an independent refrigeration
controller, and the PC should monitor it and optionally permit/disable operation.

Recommended:

- keep or install a refrigeration controller such as Eliwell IDplus, Carel Easy,
  Dixell XR series, or OVEN temperature controller;
- the vending software reads chamber temperature separately;
- the vending software blocks sales on critical temperature;
- compressor switching is done by refrigeration controller/contactor, not by a
  small hobby relay.

Links:

- Eliwell IDplus 974: https://www.eliwell.eu/en/single-stage-controller-for-refrigeration-idplus-974-1221.html
- Carel Easy refrigeration controllers: https://www.carel.com/product/easy
- OVEN TRM202 reference: https://insat.ru/products/regtrm202/

## Suggested I/O Map

This map assumes two `WB-MR6C v.3` modules on one RS-485 bus.

### Relay Outputs

| Module | Relay | Name | Function | Electrical note |
| --- | ---: | --- | --- | --- |
| R1 | K1 | `slot_A1` | Vend motor/actuator A1 | Low-voltage DC preferred. |
| R1 | K2 | `slot_A2` | Vend motor/actuator A2 | Fuse each slot. |
| R1 | K3 | `slot_B1` | Vend motor/actuator B1 | Add flyback diode/snubbers. |
| R1 | K4 | `slot_B2` | Vend motor/actuator B2 | Do not exceed relay/load rating. |
| R1 | K5 | `slot_C1` | Vend motor/actuator C1 | Confirm actual motor voltage. |
| R1 | K6 | `slot_C2` | Vend motor/actuator C2 | Confirm current under stall. |
| R2 | K1 | `window_open` | Open delivery window | Interlocked with `window_close`. |
| R2 | K2 | `window_close` | Close delivery window | Limit switch must also stop motion. |
| R2 | K3 | `cooling_permit` | Permit cooling / contactor coil | Do not directly switch compressor. |
| R2 | K4 | `light` | Cabinet/product lighting | Optional. |
| R2 | K5 | `fan` | Circulation fan | Optional. |
| R2 | K6 | `spare_alarm` | Alarm/beacon/spare | Leave spare if possible. |

### Digital Inputs

| Module | Input | Name | Function | Fail-safe preference |
| --- | ---: | --- | --- | --- |
| R1 | I1 | `service_door_closed` | Service door state | Normally closed loop. |
| R1 | I2 | `estop_ok` | Safety relay feedback | Normally closed loop. |
| R1 | I3 | `window_open_limit` | Window open limit | Direct limit switch. |
| R1 | I4 | `window_closed_limit` | Window closed limit | Direct limit switch. |
| R1 | I5 | `pickup_present` | Product/pickup optical sensor | Depends on sensor type. |
| R1 | I6 | `home_position` | Carousel/home position | Normally closed if possible. |
| R1 | I7 | `leak_or_temp_alarm` | External alarm input | Normally closed if possible. |
| R2 | I1 | `inventory_A1` | Product present A1 | Optional for MVP. |
| R2 | I2 | `inventory_A2` | Product present A2 | Optional for MVP. |
| R2 | I3 | `inventory_B1` | Product present B1 | Optional for MVP. |
| R2 | I4 | `inventory_B2` | Product present B2 | Optional for MVP. |
| R2 | I5 | `inventory_C1` | Product present C1 | Optional for MVP. |
| R2 | I6 | `inventory_C2` | Product present C2 | Optional for MVP. |
| R2 | I7 | `payout_fault` | Payout/changer fault input | Only after payout model is selected. |

### Temperature

| Sensor | Name | Placement | Purpose |
| --- | --- | --- | --- |
| T1 | `chamber_temperature` | Product chamber air | Sale blocker and status display. |
| T2 | `evaporator_temperature` | Evaporator/cooling coil | Cooling diagnostics. |
| T3 | `ambient_temperature` | Electronics area | Optional cabinet health. |

## Wiring Concepts

Only work with power removed. Mains wiring, protective earth, RCD/RCBO,
compressor contactors and inverter wiring should be done by a qualified
electrician. The diagrams below describe design intent, not permission to touch
live 220 V circuits.

### RS-485 Bus

```text
PC USB
  -> isolated USB-RS485 adapter
       A+ -------------------- A+ on R1, A+ on R2, A+ on temp module
       B- -------------------- B- on R1, B- on R2, B- on temp module
       GND/REF --------------- reference/common if required by module manual
       shield ---------------- PE at one end only, usually cabinet side
```

Rules:

- use twisted pair for A/B;
- terminate the bus at the physical ends if the run is long/noisy;
- give every module a unique Modbus address;
- label modules physically: `R1`, `R2`, `T1`;
- configure a safe state on communication loss: motors off, window stop, cooling
  policy decided separately.

### Low-Voltage DC Motor Or Solenoid Through Relay

```text
+24 VDC -> fuse -> relay COM
relay NO -> load +
load -   -> 0 VDC

Across DC load:
  diode or TVS/snubber, selected for the load and release-time requirements
```

Use this only when:

- load voltage/current is known;
- relay rating is enough for DC and inrush current;
- a stalled motor cannot overheat or destroy the mechanism before timeout.

### Delivery Window With Open/Close Directions

Preferred:

```text
R2 K1 -> OPEN command to motor driver/contactor
R2 K2 -> CLOSE command to motor driver/contactor
I3    -> open limit switch
I4    -> closed limit switch
```

Requirements:

- `OPEN` and `CLOSE` must never energize at the same time;
- there must be a software interlock in the Python adapter;
- there should be a hardware/intermediate relay interlock if possible;
- limit switches should stop motion physically, not only in software;
- use the `WB-MR6C` curtain/shutter mode if it fits the actuator.

### Cooling

Recommended design:

```text
Refrigeration controller -> compressor contactor -> compressor
PC/Modbus I/O            -> cooling permit / alarm read / temperature read
```

Do not do this as the only control:

```text
PC -> USB -> relay -> compressor
```

The compressor has startup current, short-cycle protection requirements and
safety implications. Use a real refrigeration controller and contactor.

### Emergency Stop

Bad:

```text
E-stop -> PC input only
```

Good:

```text
E-stop button -> safety relay -> cuts actuator power contactor
                         |
                         +-> feedback input `estop_ok` to Modbus I/O
```

The app should know that E-stop is active, but it must not be the only thing
stopping motors.

## Payment Strategy

There are three practical payment levels.

### MVP: Cashless Or Exact Cash, No Change

This is the fastest way to get the machine selling:

- disable payout/change;
- accept only card/QR/cashless, or exact cash if legally and operationally OK;
- vend only after confirmed payment;
- print receipt if required.

Pros:

- no payout liability;
- far fewer jams and ambiguous states;
- much easier software.

Cons:

- may reduce customer convenience;
- legal/fiscal/payment integration depends on your business setup.

### Cash With Existing DBV, No Payout

Use the existing JCM DBV-300-SD if bench-confirmed:

- DBV connects directly to the PC over RS-232;
- the app must disable/enable acceptance;
- bill events must be confirmed using documented DBV protocol or bench traces;
- no guessed protocol bytes.

This is acceptable only after real bill tests prove denominations, stacking,
rejects and fault behavior.

### Cash With Change/Payout

Recommended replacement path:

- use a documented MDB coin changer/payout/hopper system;
- connect it through `Qibixx MDB-USB`, `MDB-RS232`, or another documented
  vending payment interface;
- implement and test payout accounting separately from product vending.

Do not build payout from random relays and motors unless you are prepared to
engineer cash accounting, jam detection, empty states and recovery.

## Printer Strategy

The Custom VKP80 family is suitable for vending/kiosk receipts and commonly has
USB and RS-232 variants. The official page lists `RS232+USB`, drivers for
Windows/Linux/Virtual COM and `24 Vdc` supply for VKP80II RX.

Recommended:

1. Power printer from a proper 24 V supply.
2. Connect by USB first.
3. Install official Custom driver/tooling.
4. Print a Windows/Linux test page.
5. Later add receipt printing from the app.

If USB is unreliable, use RS-232 only after confirming cable pinout and printer
settings.

## Budget Arduino Alternative

Use this only for bench work or if the cabinet is rebuilt carefully with proper
isolation.

Minimum:

- Arduino Mega 2560;
- 2x 8-channel opto-isolated relay modules;
- opto-isolated 24 V input boards;
- DS18B20 sensor;
- 5 V DIN supply;
- 12/24 V motor supply;
- contactors/fuses/E-stop as above.

Arduino Mega official specs list many I/O pins, which is why it is more suitable
than ESP8266 for this job. But a bare Arduino board is not an industrial
controller. It needs terminal shields, input conditioning, watchdog behavior and
firmware.

Links:

- Arduino Mega 2560 Rev3: https://store-usa.arduino.cc/products/arduino-mega-2560-rev3
- CONTROLLINO outputs overview: https://www.controllino.com/outputs/
- Numato 8-channel USB relay module: https://numato.com/product/8-channel-usb-relay-module
- Advantech USB-4761 USB relay/input module: https://www.advantech.com/emt/products/1-2MLKNO/USB-4761/mod_C1E301AB-CDC8-45C0-B610-6AEA44B544AE

Arduino bench pin map if used:

| Mega pin | Function |
| ---: | --- |
| D22-D27 | slot relays A1-C2 |
| D28 | window open |
| D29 | window close |
| D30 | cooling permit |
| D31 | light |
| D34-D39 | door/window/pickup/home/E-stop status |
| D40-D45 | inventory A1-C2 |
| D46 | DS18B20 data with 4.7 kOhm pullup |

PC-to-Arduino serial command sketch should be simple text:

```text
PING
VEND A1
WINDOW OPEN
WINDOW CLOSE
COOLING ON
COOLING OFF
READ TEMP
READ INPUTS
STOP
```

Responses:

```text
OK PONG
OK VEND A1
OK TEMP 4.2
ERR TIMEOUT WINDOW_CLOSE
ERR ESTOP
```

## Software Integration Plan

The repository already has device contracts for:

- bill validator;
- change dispenser;
- motor controller;
- cooling controller;
- window controller;
- temperature sensor;
- door sensor;
- inventory sensor;
- position sensor.

Add a new adapter package such as:

```text
src/flower_vending/devices/modbus_io/
  __init__.py
  config.py
  client.py
  motor_controller.py
  window_controller.py
  cooling_controller.py
  door_sensor.py
  inventory_sensor.py
  temperature_sensor.py
```

Recommended Python dependency:

```text
pymodbus
pyserial
```

Example config shape:

```yaml
devices:
  motor_controller:
    enabled: true
    driver: modbus_io
    device_name: cabinet_modbus_motor
    settings:
      port: COM7
      baudrate: 9600
      parity: N
      stopbits: 1
      unit_outputs:
        R1:
          address: 1
          relays:
            A1: 1
            A2: 2
            B1: 3
            B2: 4
            C1: 5
            C2: 6
      pulse_ms:
        default_vend: 1500
      require_inputs:
        estop_ok: true
        service_door_closed: true

  window_controller:
    enabled: true
    driver: modbus_io
    settings:
      module: R2
      address: 2
      open_relay: 1
      close_relay: 2
      open_limit_input: 3
      closed_limit_input: 4
      motion_timeout_ms: 8000
      interlock_pause_ms: 500

  temperature_sensor:
    enabled: true
    driver: modbus_io
    settings:
      module: T1
      address: 3
      sensors:
        chamber_temperature: 1
        evaporator_temperature: 2
```

Adapter behavior:

- on startup, write all outputs OFF;
- read E-stop, service door and window limits before allowing vend;
- for `vend_slot(slot_id)`, pulse only the mapped relay, then turn it off;
- if timeout/fault occurs, turn all motion outputs off and raise a device fault;
- for window movement, enforce open/close interlock and check limit switches;
- for temperature, read Modbus value and convert to Celsius;
- log every command and physical confirmation.

## Build Phases

### Phase 1: Tabletop Bench, No 220 V Loads

Buy:

- PC or laptop;
- USB-RS485 adapter;
- one `WB-MR6C v.3`;
- 24 V supply;
- 2-3 switches;
- one small 24 V lamp or relay coil;
- one DS18B20 + temperature module.

Test:

- PC sees RS485 adapter;
- Modbus can read module inputs;
- Modbus can toggle one relay;
- E-stop/status input appears;
- temperature reads correctly;
- Python prototype can toggle a relay and read input.

No cabinet. No motors. No compressor.

### Phase 2: Cabinet Low-Voltage Rewire

Install DIN rail panel:

- 24 V power distribution;
- RS-485 bus;
- relay modules;
- input terminals;
- labels;
- fuses.

Connect only low-voltage devices first:

- door switch;
- window limit switches;
- pickup sensor;
- one test actuator or lamp.

### Phase 3: Motors And Window

For each motor:

1. Confirm voltage and stall current.
2. Select driver/relay/contactors.
3. Add fuse.
4. Add suppressor.
5. Test from local manual switch or service command.
6. Test from app.
7. Record timing.

For window:

- install open/close limit switches;
- prove that open/close cannot energize together;
- test obstruction/failure behavior;
- only then enable customer flow.

### Phase 4: Payment And Printer

Printer:

- install driver;
- print test;
- print app receipt later.

DBV:

- power with correct 12 V supply;
- connect RS-232;
- confirm port;
- run only known bench tools or documented commands;
- verify real bill insert, reject, stack and fault behavior.

Payout:

- postpone unless the model and protocol are known;
- if replacing, choose MDB payout/changer and bench it separately.

### Phase 5: Full Application Integration

Enable in config:

- simulator off;
- DBV driver confirmed;
- `modbus_io` motor/window/sensor/cooling drivers;
- safety blockers for door, E-stop, temperature and inventory;
- SQLite persistence and event logs.

Run:

- startup self-test;
- service-mode actuator tests;
- one-slot vend test;
- window open/close test;
- pickup timeout test;
- power-loss/restart test.

## Minimal First Purchase

If you want to spend the least money before committing:

1. `WB-MR6C v.3`.
2. Isolated USB-RS485 adapter.
3. Mean Well `HDR-60-24`.
4. DIN rail + terminal blocks + ferrules.
5. 3 simple limit switches.
6. One 24 V lamp or small relay coil for testing.

This lets us prove the whole PC-to-Modbus-to-relay path without touching the
old cabinet wiring.

## First Physical Job

Do this before buying the full pile:

1. Decide whether the cabinet will use the Modbus/Wiren Board route or the
   Arduino route.
2. Buy only the minimal bench kit above.
3. Build it on the table.
4. Verify one relay and one input from the PC.
5. Only after that, start cabinet rewiring.

## What Not To Do

- Do not connect the PC directly to random old relay-board pins.
- Do not switch compressor power with a small hobby relay.
- Do not make E-stop software-only.
- Do not mix 220 V and low-voltage wiring in the same loose harness.
- Do not implement payout before the payout hardware is identified.
- Do not send guessed DBV protocol bytes.
- Do not buy all motors/drivers before measuring actual motor voltage/current.

## Practical Buying Sources

For Russia/CIS-style sourcing:

- Wiren Board official shop for WB modules.
- OVEN official shop or distributors for PR/MV/MU modules.
- Mean Well Russia/distributors for power supplies.
- Chip Dip, Platan, Terraelectronica, Promelec-type suppliers for terminals,
  relays, contactors, Omron/Finder/Schneider parts.
- Ozon/AliExpress only for bench-grade Arduino modules, not for final safety
  components.
- Refrigeration parts suppliers for Eliwell/Carel/Dixell controllers.
- Vending/payment suppliers for MDB changers, Nayax/Vendotek/Qibixx hardware.

## Decision

For this machine, the recommended replacement is:

```text
PC + existing/confirmed DBV + existing/confirmed VKP80 printer
+ RS485 Modbus I/O cabinet based on WB-MR6C modules
+ independent refrigeration controller
+ professional E-stop/contactors/fusing
+ no payout in MVP unless a documented MDB payout/changer is selected
```

This gives the shortest path from a dead undocumented cabinet to a system that
can be tested, logged, supported and eventually integrated with
`flower-vending-system`.
