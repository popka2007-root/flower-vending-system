"""Machine-level domain event factories."""

from flower_vending.domain.events import DomainEvent


def machine_event(
    event_type: str,
    correlation_id: str,
    **payload: object,
) -> DomainEvent:
    return DomainEvent(
        event_type=event_type,
        correlation_id=correlation_id,
        payload=payload,
    )
