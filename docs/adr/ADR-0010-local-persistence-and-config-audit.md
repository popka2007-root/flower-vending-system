# ADR-0010: Local Persistence and Configuration Audit

## Status

Accepted

## Context

The machine needs durable local persistence for catalog data, transaction state, recovery evidence, service audit, and device configuration. Recovery must remain journal-first, while configuration must remain platform- and device-specific infrastructure rather than bleeding into the application or domain layers.

We also need to preserve the known `COM3` deployment fact for the DBV-300-SD without hardcoding it into business logic.

## Decision

We use:

- local SQLite as the durable machine store;
- an append-only `transaction_journal` as the recovery evidence log;
- repository classes for operational projections and audit records;
- YAML as the human-managed bootstrap configuration format;
- structured rotating JSON logs for diagnostics.

Configuration is loaded into typed infrastructure models, then converted into existing runtime contracts such as `DBV300SDValidatorConfig`.

Applied configuration and effective device settings are also snapshotted into SQLite for audit.

## Consequences

### Positive

- Recovery evidence stays durable and queryable locally.
- Configuration remains editable and deployment-friendly.
- The known `COM3` fact is preserved only where it belongs: infrastructure configuration.
- Journal, projections, and diagnostic logs each serve separate roles.

### Negative

- SQLite schema and serializers must be maintained carefully.
- Nullable aggregate snapshots require explicit serialization discipline.
- The bootstrap path will need additional wiring in later phases to use repositories directly.

## Rejected alternatives

- flat file persistence without a queryable local database
- diagnostic logs as the only recovery source
- hardcoding device ports and timeouts in application services
- storing only the latest machine snapshot without an append-only transaction journal
