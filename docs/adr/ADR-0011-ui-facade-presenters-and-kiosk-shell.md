# ADR-0011: UI Facade, Presenter Layer, and Kiosk Shell

## Status

Accepted

## Context

The project needs a touch-friendly kiosk UI and technician screens, but the UI must not become the workflow authority. The application core already owns commands, events, FSM transitions, and device orchestration.

Without an explicit UI boundary, Qt widgets would quickly start:

- reading and mutating application state directly;
- reimplementing payment rules;
- coupling to device or persistence details;
- becoming impossible to test headlessly.

## Decision

We implement the UI with four layers:

- a UI-facing facade over `ApplicationCore`;
- immutable screen view models;
- presenters that translate snapshots and events into those view models;
- PySide6 widgets bound to presenter output.

Navigation uses a stacked-window shell with explicit screen identifiers.

Qt widgets emit user intent only. They do not perform business decisions.

## Consequences

### Positive

- The UI remains replaceable and testable.
- Presenter behavior can run headlessly on simulators.
- Customer and service flows can share one window shell without sharing business logic.
- The event bus becomes a natural bridge from application state to live UI updates.

### Negative

- More mapping code is required between snapshots and view models.
- A Qt/asyncio bootstrap integration is still needed at runtime.

## Rejected alternatives

- putting payment and vend rules directly in screen controllers
- letting Qt views call hardware adapters directly
- treating screen state as the workflow source of truth
- building a UI-specific demo flow separate from the real application core
