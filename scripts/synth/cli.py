"""CLI to generate a scenario and send it to the platform via the SDK.

Example:
    python -m scripts.synth.cli db_outage --duration 120 --seed 42
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime
from random import Random

from watchdog_client import EventCreate, WatchdogClient

from .registry import SCENARIOS, get_scenario
from .scenarios.base import GeneratedEvent

BATCH_SIZE = 1000

ClientFactory = Callable[[str], WatchdogClient]


def chunked(items: Sequence[GeneratedEvent], size: int) -> Iterator[list[GeneratedEvent]]:
    for index in range(0, len(items), size):
        yield list(items[index : index + size])


def to_event_create(event: GeneratedEvent) -> EventCreate:
    return EventCreate(
        service=event.service,
        level=event.level,
        message=event.message,
        timestamp=event.timestamp,
        metadata=event.metadata,
    )


def _default_client_factory(api_url: str) -> WatchdogClient:
    return WatchdogClient(base_url=api_url)


def run(args: argparse.Namespace, client_factory: ClientFactory = _default_client_factory) -> int:
    """Generate the scenario and (unless --dry-run) send it. Returns event count."""
    scenario = get_scenario(args.scenario)
    events = list(
        scenario.generate(
            start=datetime.now(tz=UTC),
            duration_seconds=args.duration,
            rng=Random(args.seed),
        )
    )
    if args.dry_run:
        return len(events)
    sent = 0
    with client_factory(args.api_url) as client:
        for batch in chunked(events, BATCH_SIZE):
            client.create_batch([to_event_create(event) for event in batch])
            sent += len(batch)
    return sent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthetic traffic generator")
    parser.add_argument("scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=int, default=120)
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    count = run(args)
    verb = "generated" if args.dry_run else "sent"
    print(f"{verb} {count} events for scenario '{args.scenario}'")


if __name__ == "__main__":
    main()
