"""Command-line entrypoints for simulator-safe workflows."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from flower_vending.devices.dbv300sd.bench import DBV300SDSerialSmokeBench, parse_hex_bytes
from flower_vending.devices.dbv300sd.config import SerialTransportSettings
from flower_vending.devices.exceptions import DeviceAdapterError
from flower_vending.runtime.bootstrap import (
    BootstrapReport,
    build_simulator_environment,
    discover_project_root,
    validate_config_file,
)
from flower_vending.simulators.scenarios.catalog import run_default_scenario_suite


def build_parser() -> argparse.ArgumentParser:
    project_root = discover_project_root()
    default_config = project_root / "config" / "examples" / "machine.simulator.yaml"

    parser = argparse.ArgumentParser(prog="python -m flower_vending")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_config_argument(target: argparse.ArgumentParser) -> None:
        target.add_argument(
            "--config",
            default=str(default_config),
            help="Path to the YAML configuration file.",
        )
        target.add_argument(
            "--json",
            action="store_true",
            help="Render the command output as JSON.",
        )

    validate_parser = subparsers.add_parser("validate-config", help="Validate configuration and bootstrap checks.")
    add_config_argument(validate_parser)
    validate_parser.add_argument(
        "--prepare",
        action="store_true",
        help="Create runtime directories such as var/data and var/log when they are missing.",
    )

    diagnostics_parser = subparsers.add_parser("diagnostics", help="Start simulator runtime and print diagnostics.")
    add_config_argument(diagnostics_parser)

    service_parser = subparsers.add_parser("service", help="Enter service mode and print a service snapshot.")
    add_config_argument(service_parser)
    service_parser.add_argument("--operator", default="technician", help="Service operator identifier.")
    service_parser.add_argument(
        "--action",
        action="append",
        default=[],
        help="Optional simulator action to apply before printing the service report.",
    )

    runtime_parser = subparsers.add_parser("simulator-runtime", help="Run simulator runtime or deterministic scenarios.")
    add_config_argument(runtime_parser)
    runtime_parser.add_argument(
        "--duration",
        type=float,
        default=0.0,
        help="Keep the runtime alive for the given number of seconds before shutting down.",
    )
    runtime_parser.add_argument(
        "--scenario",
        action="append",
        default=[],
        help="Deterministic scenario name to run. May be passed multiple times.",
    )
    runtime_parser.add_argument(
        "--use-config-scenarios",
        action="store_true",
        help="Run the scenario suite listed in config.simulator.scenario_suite.",
    )

    ui_parser = subparsers.add_parser("simulator-ui", help="Launch the simulator kiosk UI.")
    ui_parser.add_argument(
        "--config",
        default=str(default_config),
        help="Path to the YAML configuration file.",
    )

    bench_parser = subparsers.add_parser(
        "dbv300sd-serial-smoke",
        help="Open DBV-300-SD serial transport and optionally exchange explicit raw bytes.",
    )
    bench_parser.add_argument("--port", required=True, help="Serial port path, for example COM3.")
    bench_parser.add_argument("--baudrate", type=int, default=9600, help="Serial baud rate.")
    bench_parser.add_argument("--bytesize", type=int, default=8, help="Serial byte size.")
    bench_parser.add_argument("--parity", default="N", help="Serial parity.")
    bench_parser.add_argument("--stopbits", type=int, default=1, help="Serial stop bits.")
    bench_parser.add_argument("--read-timeout-s", type=float, default=0.2, help="Read timeout.")
    bench_parser.add_argument("--write-timeout-s", type=float, default=0.2, help="Write timeout.")
    bench_parser.add_argument(
        "--trace-log",
        default=str(project_root / "var" / "log" / "dbv300sd-bench-trace.jsonl"),
        help="Dedicated JSONL bench log for serial settings and raw rx/tx frames.",
    )
    bench_parser.add_argument(
        "--tx-hex",
        help="Explicit raw bytes to transmit, e.g. '01 02 FF'. No bytes are sent if omitted.",
    )
    bench_parser.add_argument(
        "--read-size",
        type=int,
        default=0,
        help="Read this many bytes after --tx-hex is written. Requires --tx-hex.",
    )
    bench_parser.add_argument("--correlation-id", help="Optional trace correlation id.")
    bench_parser.add_argument("--note", help="Optional trace note.")
    bench_parser.add_argument(
        "--json",
        action="store_true",
        help="Render the command output as JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-config":
        return _command_validate_config(args)
    if args.command == "diagnostics":
        return asyncio.run(_command_diagnostics(args))
    if args.command == "service":
        return asyncio.run(_command_service(args))
    if args.command == "simulator-runtime":
        return asyncio.run(_command_simulator_runtime(args))
    if args.command == "simulator-ui":
        from flower_vending.runtime.ui_runner import run_simulator_ui

        return run_simulator_ui(config_path=args.config)
    if args.command == "dbv300sd-serial-smoke":
        return asyncio.run(_command_dbv300sd_serial_smoke(args, parser))
    parser.error(f"unsupported command: {args.command}")


def _command_validate_config(args: argparse.Namespace) -> int:
    config, _, report = validate_config_file(args.config, prepare_directories=args.prepare)
    payload = {
        "valid": report.valid,
        "machine_id": config.machine.machine_id,
        "resource_root": str(report.project_root),
        "state_root": str(report.state_root),
        "created_directories": [str(path) for path in report.created_directories],
        "messages": [asdict(message) for message in report.messages],
        "platform": report.platform_profile.target_os,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print_report(report)
    return 0 if report.valid else 1


async def _command_diagnostics(args: argparse.Namespace) -> int:
    environment = await build_simulator_environment(config_path=args.config, prepare_directories=True)
    await environment.start()
    try:
        payload = environment.diagnostics_report()
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(_format_diagnostics(payload))
        return 0
    finally:
        await environment.stop()


async def _command_service(args: argparse.Namespace) -> int:
    environment = await build_simulator_environment(config_path=args.config, prepare_directories=True)
    await environment.start()
    try:
        for action_id in args.action:
            await environment.simulator_controls.execute_action(
                action_id,
                correlation_id=environment.ui_facade.new_correlation_id(),
            )
        payload = await environment.service_report(operator_id=args.operator)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(_format_service(payload))
        return 0
    finally:
        await environment.stop()


async def _command_simulator_runtime(args: argparse.Namespace) -> int:
    validate_config_file(args.config, prepare_directories=True)
    scenario_names = tuple(args.scenario)
    if args.use_config_scenarios:
        config, _, _ = validate_config_file(args.config, prepare_directories=True)
        scenario_names = tuple(config.simulator.scenario_suite)
    if scenario_names:
        results = await run_default_scenario_suite(scenario_names)
        scenario_payload = [asdict(result) for result in results]
        if args.json:
            print(json.dumps(scenario_payload, ensure_ascii=False, indent=2))
        else:
            print(_format_scenarios(results))
        return 0 if all(result.success for result in results) else 1

    environment = await build_simulator_environment(config_path=args.config, prepare_directories=True)
    await environment.start()
    try:
        diagnostics_payload = environment.diagnostics_report()
        if args.json:
            print(json.dumps(diagnostics_payload, ensure_ascii=False, indent=2))
        else:
            print(_format_diagnostics(diagnostics_payload))
        if args.duration > 0:
            await asyncio.sleep(args.duration)
        return 0
    finally:
        await environment.stop()


async def _command_dbv300sd_serial_smoke(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> int:
    if args.read_size > 0 and args.tx_hex is None:
        parser.error("--read-size requires --tx-hex so bench reads are tied to explicit raw bytes")
    try:
        tx_payload = parse_hex_bytes(args.tx_hex) if args.tx_hex is not None else None
        settings = SerialTransportSettings(
            port=args.port,
            baudrate=args.baudrate,
            bytesize=args.bytesize,
            parity=args.parity,
            stopbits=args.stopbits,
            read_timeout_s=args.read_timeout_s,
            write_timeout_s=args.write_timeout_s,
        )
        bench = DBV300SDSerialSmokeBench(settings=settings, trace_log=Path(args.trace_log))
        result = await bench.run(
            tx_payload=tx_payload,
            read_size=args.read_size,
            correlation_id=args.correlation_id,
            note=args.note,
        )
    except DeviceAdapterError as exc:
        print(f"DBV-300-SD serial smoke failed: {exc}")
        return 1

    payload = result.to_json_payload()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_format_dbv300sd_serial_smoke(payload))
    return 0


def _print_report(report: BootstrapReport) -> None:
    print(f"Config: {report.config_path}")
    print(f"Resource root: {report.project_root}")
    print(f"State root: {report.state_root}")
    if report.created_directories:
        print("Created directories:")
        for path in report.created_directories:
            print(f"  - {path}")
    if report.messages:
        print("Messages:")
        for message in report.messages:
            print(f"  - [{message.severity}] {message.code}: {message.message}")
    else:
        print("Messages: none")


def _format_diagnostics(payload: dict[str, Any]) -> str:
    lines = [
        f"Machine state: {payload['machine']['machine_state']}",
        "Sale blockers: " + (", ".join(payload["machine"]["sale_blockers"]) or "none"),
        "Devices:",
    ]
    lines.extend(f"  - {device['device_name']}: {device['state']}" for device in payload["devices"])
    lines.append("Recent events:")
    if payload["recent_events"]:
        lines.extend(f"  - {item['event_type']} [{item['correlation_id']}] {item['summary']}" for item in payload["recent_events"])
    else:
        lines.append("  - none")
    lines.append("Platform extension points:")
    lines.extend(
        f"  - {item['name']}: {item['status']} ({item['mode']})"
        for item in payload["platform"]["extension_points"]
    )
    return "\n".join(lines)


def _format_service(payload: dict[str, Any]) -> str:
    lines = [
        f"Operator: {payload['operator_id']}",
        f"Machine state: {payload['machine_state']}",
        "Sale blockers: " + (", ".join(payload["sale_blockers"]) or "none"),
    ]
    if payload["unresolved_transaction_ids"]:
        lines.append("Unresolved transactions: " + ", ".join(payload["unresolved_transaction_ids"]))
    else:
        lines.append("Unresolved transactions: none")
    lines.append("Recent events:")
    if payload["recent_events"]:
        lines.extend(f"  - {item['event_type']} [{item['correlation_id']}] {item['summary']}" for item in payload["recent_events"])
    else:
        lines.append("  - none")
    return "\n".join(lines)


def _format_scenarios(results: tuple[Any, ...]) -> str:
    lines: list[str] = []
    for result in results:
        status = "PASS" if result.success else "FAIL"
        lines.append(f"{status}: {result.scenario_name} ({result.machine_state})")
        for note in result.notes:
            lines.append(f"  - {note}")
        for error in result.errors:
            lines.append(f"  - error: {error}")
    return "\n".join(lines)


def _format_dbv300sd_serial_smoke(payload: dict[str, Any]) -> str:
    serial = payload["serial_settings"]
    lines = [
        f"Transport: {payload['transport_name']}",
        (
            "Serial: "
            f"port={serial['port']} baudrate={serial['baudrate']} "
            f"bytesize={serial['bytesize']} parity={serial['parity']} "
            f"stopbits={serial['stopbits']} read_timeout_s={serial['read_timeout_s']} "
            f"write_timeout_s={serial['write_timeout_s']}"
        ),
        f"Trace log: {payload['trace_log']}",
        f"Opened: {payload['opened']}",
        f"Wrote bytes: {payload['wrote_bytes']}",
        f"Read bytes: {payload['read_bytes']}",
    ]
    if payload["rx_payload_hex"]:
        lines.append(f"RX payload hex: {payload['rx_payload_hex']}")
    lines.append(f"Note: {payload['note']}")
    return "\n".join(lines)
