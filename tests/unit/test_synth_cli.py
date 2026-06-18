"""Tests for the synthetic traffic CLI."""

from datetime import UTC, datetime

from scripts.synth.cli import chunked, main, parse_args, run, to_event_create
from scripts.synth.scenarios.base import GeneratedEvent


class _FakeClient:
    def __init__(self) -> None:
        self.batches: list[list] = []

    def create_batch(self, events: list) -> None:
        self.batches.append(events)

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _event(i: int) -> GeneratedEvent:
    return GeneratedEvent("svc", "INFO", f"m{i}", datetime(2026, 6, 18, tzinfo=UTC))


class TestChunked:
    def test_splits_into_max_size_chunks(self):
        chunks = list(chunked([_event(i) for i in range(2500)], 1000))

        assert [len(c) for c in chunks] == [1000, 1000, 500]


class TestToEventCreate:
    def test_maps_fields(self):
        created = to_event_create(_event(1))

        assert created.service == "svc"
        assert created.level == "INFO"


class TestRun:
    def test_dry_run_counts_without_client(self):
        args = parse_args(["normal", "--duration", "30", "--dry-run"])

        count = run(args, client_factory=_fail_if_called)

        assert count > 0

    def test_sends_in_batches_under_limit(self):
        client = _FakeClient()
        args = parse_args(["black_friday", "--duration", "120", "--seed", "42"])

        sent = run(args, client_factory=lambda _url: client)

        assert sent > 1000
        assert sum(len(b) for b in client.batches) == sent
        assert all(len(b) <= 1000 for b in client.batches)


def _fail_if_called(_url: str):
    raise AssertionError("client should not be constructed for a dry run")


class TestParseAndMain:
    def test_parse_args_defaults(self):
        args = parse_args(["normal"])

        assert args.seed == 42
        assert args.duration == 120
        assert args.api_url == "http://localhost:8000"
        assert args.dry_run is False

    def test_main_dry_run_prints_count(self, capsys):
        main(["normal", "--duration", "10", "--dry-run"])

        captured = capsys.readouterr()
        assert "generated" in captured.out
        assert "normal" in captured.out
