# Phase 8 - UI

## Scope of this phase

This phase implements the kiosk-facing UI structure on top of the already accepted application core.

The goals are:

- keep UI separate from domain, application orchestration, and device integration;
- introduce a presenter/view-model layer for touch screens;
- provide a kiosk-oriented navigation model;
- add concrete PySide6 screen widgets and a main window shell;
- show how UI consumes `ApplicationCore` safely through a dedicated facade;
- support customer screens, technician screens, and diagnostics screens without embedding business rules inside Qt widgets.

## Architectural alignment

This phase does not revise previous decisions.

Instead, it closes a small implementation gap: service and recovery commands already existed in the domain model, but application-core wiring for service mode and explicit recovery commands had not yet been connected. This phase wires those handlers in the application layer so the UI can invoke them through accepted orchestration boundaries.

That is an implementation completion step, not an architecture change.

## Implemented UI layering

The UI package is now split into:

- `ui/navigation.py`
- `ui/session.py`
- `ui/facade.py`
- `ui/viewmodels/`
- `ui/presenters/`
- `ui/widgets/`
- `ui/views/`
- `ui/theme.py`

### Responsibilities

`navigation.py` holds kiosk navigation state and screen identifiers.

`session.py` holds only presentation-side session state such as the selected product, active transaction id, accepted amount snapshot, and last user-facing error text.

`facade.py` is the only bridge from presenters to `ApplicationCore`. It exposes read-side snapshots and command-driven operations for:

- catalog browsing;
- start purchase and start cash session;
- cancel purchase;
- confirm pickup;
- enter and exit service mode;
- trigger recovery for an interrupted transaction.

`viewmodels/` contains typed immutable screen models.

`presenters/` maps application snapshots and domain events into screen view models.

`widgets/` contains reusable touch controls.

`views/` contains PySide6 screen widgets and the main stacked-window shell.

## Implemented presenter layer

The presenter layer now includes:

- `CatalogPresenter`
- `PaymentPresenter`
- `StatusPresenter`
- `ServicePresenter`
- `KioskPresenter`

### KioskPresenter

`KioskPresenter` is the top-level UI workflow object. It owns:

- navigation state;
- presentation session state;
- subscriptions to application-domain events;
- screen rendering decisions;
- translation of UI actions into facade calls.

It is intentionally not a second application orchestrator. It never talks to hardware and it never reimplements FSM rules.

It only:

- asks the application layer for snapshots;
- dispatches accepted commands through the facade;
- reacts to normalized domain events from the event bus;
- chooses which screen view model should be shown next.

## Implemented view models

The view-model layer now covers:

- catalog screen;
- product details card;
- payment screen;
- exact-change screen;
- delivery progress screen;
- pickup screen;
- error screen;
- sales-blocked screen;
- service screen;
- diagnostics screen.

Each view model is plain immutable data. Qt widgets only bind to that data and emit UI intent signals back upward.

## Implemented kiosk navigation

The navigation model includes the following user-facing screens:

- `HOME`
- `CATALOG`
- `PRODUCT_DETAILS`
- `PAYMENT`
- `EXACT_CHANGE`
- `DISPENSING`
- `PICKUP`
- `ERROR`
- `SALES_BLOCKED`
- `SERVICE`
- `DIAGNOSTICS`

Important behavior:

- `HOME` can redirect to `EXACT_CHANGE` when the machine is in exact-change-only mode.
- sale blockers redirect customer flow to `SALES_BLOCKED`.
- confirmed payment and payout progress redirect to `DISPENSING`.
- delivery window open redirects to `PICKUP`.
- service and diagnostics remain accessible to technician workflows.

## Implemented screens

Concrete PySide6 widgets now exist for:

- catalog/home screen
- product details screen
- payment screen
- status/error/exact-change/sales-blocked screen
- delivery/progress/pickup screen
- service screen
- diagnostics screen

The `KioskMainWindow` uses a `QStackedWidget` and binds those screens to `ScreenRender` objects produced by the presenter.

## Kiosk-friendly UI decisions

The Qt layer uses:

- large touch buttons;
- high-contrast labels;
- stacked layouts with low interaction density;
- reusable card surfaces;
- explicit warning/error banners;
- a warm, product-appropriate visual theme instead of a generic dark industrial dashboard.

This keeps the kiosk readable in customer mode while still exposing dense diagnostics only inside service screens.

## Example integration with application layer

The application-facing path is:

1. Qt widget emits user intent
2. `KioskMainWindow` schedules presenter action
3. `KioskPresenter` calls `UiApplicationFacade`
4. `UiApplicationFacade` dispatches application commands or reads snapshots
5. `ApplicationCore` and event bus perform the real workflow
6. `KioskPresenter` receives normalized domain events
7. presenter emits the next `ScreenRender`
8. Qt view binds the new screen model

This preserves the required separation:

- Qt widgets do not touch domain entities directly;
- Qt widgets do not call device adapters;
- presenters do not implement payment or vend rules;
- the application core remains the workflow authority.

## Application-core additions made for UI integration

Two small additions were made to support safe UI integration:

- `InventoryService` now exposes read-side listing methods used by the catalog presenter.
- `ServiceModeCoordinator` was added and wired into `build_application_core(...)`, together with command-bus registration for `EnterServiceMode` and `RecoverInterruptedTransaction`.

These changes close missing integration seams and stay consistent with earlier ADRs.

## Verification performed

### Successful verification

The following verification completed successfully:

- `py_compile` over the full `src/` tree;
- a headless presenter smoke run using the real `SimulationHarness` from Phase 6.

The headless UI smoke confirmed the presenter path:

- `home`
- `product_details`
- `payment`
- `pickup`
- `home`

This verifies that the UI presenter/facade layer is sitting on the real application core instead of a demo-only flow.

### Environment limitation

The concrete PySide6 widgets and `KioskMainWindow` were not import-run in this shell because `PySide6` is not installed in the active interpreter environment.

The Qt files were still syntax-validated through `py_compile`, but interactive UI runtime validation remains pending until the optional UI dependency is installed.

## Assumptions

- The kiosk runtime will provide a compatible `asyncio`/Qt integration so `asyncio.create_task(...)` can be used from UI callbacks.
- One active customer transaction remains the intended kiosk model.
- Catalog and service screens may share the same underlying stacked-window shell.
- Service authentication and technician authorization are outside this phase and remain a later extension point.

## Fully implemented

- UI navigation model
- presentation session state
- application-facing UI facade
- presenter/view-model layer
- concrete PySide6 screen widgets
- main stacked-window kiosk shell
- service and diagnostics screens
- exact-change and sales-blocked customer screens
- headless smoke validation of presenter flow

## Scaffolded

- technician authentication and role checks
- richer diagnostics actions such as acknowledge-fault and reconcile cash inventory
- a dedicated UI adapter for persisted repositories and service audit history
- a production `Qt <-> asyncio` runner or qasync-style bootstrap
- localized strings and theming profiles

## Requires hardware confirmation

- none for basic UI structure itself
- real touchscreen calibration, driver behavior, and kiosk-shell deployment remain platform validation work
- any technician actions that depend on real device acknowledgements or reconcile procedures remain tied to later hardware-backed phases
