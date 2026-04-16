# DBV-300-SD Bench Validation Plan

This plan prepares the DBV-300-SD layer for real hardware without treating any
unconfirmed wire behavior as production truth. The current production protocol
bindings must remain the deferred implementations until the checks below are
completed with vendor documentation or bench captures.

## Safety Rules

- Do not add DBV-300-SD command bytes, checksums, handshakes, retry policies, or
  event maps from guesses.
- Run bench smoke from the CLI with explicit operator-provided raw bytes only:
  `python -m flower_vending dbv300sd-serial-smoke --port <port>`.
- Keep bench logs separate from application logs. Raw rx/tx frames belong in the
  dedicated JSONL trace log.
- Keep COM port names in configuration or CLI arguments. Do not hardcode COM3 in
  core, application, or adapter logic.

## What Must Be Confirmed

- Physical mode used by the installed DBV-300-SD: serial, MDB, pulse-like, or a
  controller-specific bridge.
- Serial parameters: port name, baudrate, byte size, parity, stop bits, read and
  write timeouts, and whether hardware/software flow control is required.
- Frame structure: start/end markers, length fields, addressing, checksums,
  escaping, acknowledgements, negative acknowledgements, and retry behavior.
- Startup handshake and the sequence needed to reach an idle disabled state.
- Acceptance enable/disable behavior and whether disabling is acknowledged.
- Polling or push-event model, including idle responses and no-data responses.
- Escrow support, stack/return semantics, and the exact events emitted for each.
- Bill denomination mapping and currency assumptions.
- Fault, jam, cassette, disabled, power-cycle, and reset reporting.
- Recovery behavior after transport loss, process restart, validator reset, and
  bill-in-path ambiguity.

## Timings To Measure

- Port open latency and first readable response time after power-on.
- Minimum safe delay after startup before sending the first command.
- Typical and worst-case response latency for every confirmed command.
- Poll interval bounds that avoid missed events and avoid bus/device overload.
- Ack/nack timeout, retry spacing, and retry count before declaring a fault.
- Time from bill insertion to detected, validated, escrow, stacked, returned, or
  rejected events.
- Acceptance disable latency while idle and while a bill is in progress.
- Transport recovery timing after unplug/replug or validator power cycle.

## Validator Events To Capture

For each capture, keep the raw trace frame, timestamp, correlation id, operator
note, expected physical action, and observed machine state.

- Idle poll/no-event response.
- Bill detected.
- Bill validated with every accepted denomination.
- Bill rejected for an unsupported or unreadable bill.
- Escrow available, if escrow is confirmed.
- Escrow stacked, if escrow is confirmed.
- Escrow returned, if escrow is confirmed.
- Validator disabled after an explicit disable command.
- Cassette removed/full, bill path jam, sensor fault, and communication fault.
- Startup reset/power-cycle events.
- Ambiguous events where a bill may be in path during restart or transport loss.

## Trace Format

Raw rx/tx frames are recorded as JSONL records with:

- `timestamp`: timezone-aware timestamp.
- `direction`: `rx` or `tx`.
- `raw_bytes_hex`: space-separated uppercase hex bytes.
- `correlation_id`: optional operator or test correlation id.
- `note`: optional operator note.

The bench tool may also write metadata records such as serial parameters to the
same dedicated bench log. Production application logs must not be used as the
primary protocol capture.

## Criteria To Enable A Real Protocol Implementation

- Official documentation or bench captures explain every byte used by the first
  implementation.
- A real `DBV300Protocol` implementation passes the DBV300 protocol conformance
  tests with a fake transport and has bench-specific tests for confirmed frames.
- Startup, disable, enable, poll, shutdown, fault, and recovery behavior are
  validated on the bench with timestamped traces.
- Event mapping to `ValidatorProtocolEvent` is documented for every supported
  validator event and fault.
- Timeouts and retries are backed by measured data, not simulator assumptions.
- Deferred protocols remain available as the default production-safe fallback
  until the deployment configuration explicitly selects the confirmed
  implementation.
