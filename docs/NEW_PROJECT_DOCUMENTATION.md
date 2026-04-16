Flower Vending System Documentation
Overview

The Flower Vending System is a simulator‑driven platform designed to model the operation of a flower vending machine. It provides a production‑like software baseline that can run without real hardware. The simulator demonstrates a complete workflow including the application core and finite‑state machine (FSM), configurable devices, a kiosk user interface, recovery patterns and a SQLite‑based runtime state. This allows developers and operators to validate designs, test scenarios and present demos without connecting to physical vending hardware.

Key capabilities include:

A platform‑neutral domain/application core with an event bus, command bus and journal‑backed recovery patterns.
Deterministic simulator devices (bill validator, payout, motors, sensors) that implement the same contracts expected from hardware adapters.
Multiple entrypoints such as simulator runtime, diagnostics, service mode and kiosk UI.
Unified CLI via python -m flower_vending … for common operations.
Desktop builds for Windows and Linux (portable executables and installers).

Real hardware integration (bill validators, payout mechanisms, motors, sensors and other components) is intentionally left incomplete and requires bench validation before release.

Architecture

The project follows a layered architecture with clear separation between domain logic, application orchestration, infrastructure, device abstractions and user interface. The source tree in src/flower_vending contains the following major subpackages:

Module	Purpose
app	Application‑level orchestration and entrypoints for different runtime modes (simulator, diagnostics, service, etc.).
cooling	Control logic for temperature management and cooling devices.
devices	Abstract interfaces and simulator implementations for hardware devices (bill validator, payout, motors, sensors).
domain	Core domain entities, commands, events and FSM definitions; includes journal‑backed recovery patterns.
infrastructure	Persistence, configuration, logging and external service integrations.
inventory	Management of product inventory and catalog.
payments	Payment processing logic, including cash transactions and change handling.
platform	Platform abstractions for Windows/Linux differences, including service wrappers and kiosk shell launchers.
runtime	Central runtime loop coordinating devices, domain logic and event dispatch.
simulators	Deterministic simulators for each hardware device with fault injection and scenario control.
telemetry	Logging, metrics and diagnostic reporting.
ui	Presentation layer and kiosk user interface built with Qt/PySide; presenters and view‑models wire the domain to the UI.
vending	High‑level vending workflows (product selection, purchase, delivery and recovery).

This structure allows developers to extend or swap out components (e.g., implementing a real bill validator adapter) without affecting the rest of the system.

Event‑Driven Design

The core uses an event bus and command bus to decouple producers from consumers. Domain services emit events when significant actions occur (e.g., money inserted, product dispensed). Handlers listen on the event bus to drive FSM transitions, persist journal entries and update the UI.

Device Abstractions

Every hardware device is represented by an interface describing its commands and event callbacks. Simulator implementations live alongside these interfaces; they provide deterministic behavior and fault injection (e.g., bill jam, temperature fault). A real adapter can later implement the same interface and be bench‑validated to meet the contract.

Getting Started

Install dependencies on a clean Python environment:

python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-ui.txt

For editable installs with extras use:

python -m pip install -e ".[dev,ui]"

Prepare configuration and runtime directories by validating the example config:

python -m flower_vending validate-config --config config\examples\machine.simulator.yaml --prepare

Run the simulator runtime using the example configuration:

python -m flower_vending simulator-runtime --config config\examples\machine.simulator.yaml

Launch diagnostics or service mode to inspect internal state or perform maintenance:

python -m flower_vending diagnostics --config config\examples\machine.simulator.yaml
python -m flower_vending service --config config\examples\machine.simulator.yaml

Start the simulator UI (kiosk interface):

python -m flower_vending simulator-ui --config config\examples\machine.simulator.yaml

Verify the project by running the comprehensive verification script:

python scripts\verify_project.py

This script validates the config, compiles the package, runs unit/integration tests and performs smoke tests across simulator modes.

Desktop Releases

Pre‑packaged desktop builds are available for end users who do not want to install Python:

Windows: FlowerVendingSimulator-Windows-x64.exe (portable) and FlowerVendingSimulator-Setup-Windows-x64.exe (installer).
Linux: FlowerVendingSimulator-Linux-x86_64.AppImage (portable) and FlowerVendingSimulator-Linux-x86_64.tar.gz (self‑contained bundle).

Release artifacts are built via GitHub Actions when tags (e.g., v0.1.0) are pushed. Scripts in scripts/ (build-windows-release.bat and build-linux-release.sh) allow local builds.

Documentation Map

The docs folder contains comprehensive guides:

Production Readiness Boundary – details capabilities and pending hardware integration.
Operations Runbook – instructions for operating, maintaining and troubleshooting the simulator.
Platform Abstractions – explains how platform differences (Windows vs Linux) are isolated.
Project Documentation (RU), User Guide (RU), Developer Guide (RU) and Technical Guide (RU) – Russian‑language versions of project, user, developer and technical documentation.
Architecture Decision Records (ADR) – numbered ADR files documenting architectural choices (layered architecture, journal‑first recovery, cash transaction safety, platform isolation, FSM authority, device contracts, application orchestration, simulator harness, persistence and config audit, UI façade, test strategy, hardware enablement).

Each ADR captures the context, decision and consequences for a particular design choice. Reviewing these files provides insight into why the system is structured as it is.

File Structure

Aside from the main source tree, the repository includes:

config/examples – Sample YAML configurations for Linux, Windows and simulator machines.
scripts – Helper scripts for validation, running simulator modes, resetting demo data and building releases.
packaging – Packaging assets and a build_release.py script; includes Windows‑specific resources.
tests – Unit and integration tests covering config validation, domain logic, simulator scenarios and recovery behavior.
Outdated / Unnecessary Artifacts

During review, a few items appear outdated or redundant:

Legacy documentation in Word format: docs/flower-vending-system-project-documentation.docx duplicates material already covered in markdown guides. Maintaining only the markdown version simplifies version control and collaboration.
Site customization (sitecustomize.py): This module modifies the Python import path for docs generation. If not used by your build process, consider removing or integrating its logic into a setup script.
Duplicate Russian guides: There are multiple Russian‑language guides (project, user, developer, technical). Consolidating them or generating them from a single source of truth (e.g., using Sphinx with translations) will reduce drift.
Example configuration for outdated platforms: Ensure the config/examples/machine.windows.yaml and machine.linux.yaml reflect current hardware assumptions; remove or archive old configs if they no longer match the simulator.

Before deletion, confirm that these files are not referenced in build scripts or documentation.

Contributing & Future Work

The project is simulator‑first by design. Future work includes implementing and bench‑validating real hardware adapters (bill validator, payout, motor/carousel, sensors), ensuring platform autostart and kiosk lockdown, adding pickup confirmation sensors and satisfying regional safety regulations. Contributions are welcome in the form of new device adapters, UI enhancements, translations and documentation improvements.
