"""Unit tests for event normalization (signatures + level standardization)."""

import pytest
from backend.app.core.exceptions import EventValidationError
from backend.app.ingestion.normalizer import generate_signature, normalize_level
from backend.app.models.enums import LogLevel


class TestGenerateSignature:
    def test_strips_integer_numbers(self):
        assert generate_signature("Retried 5 times") == "Retried <NUM> times"

    def test_strips_decimal_numbers(self):
        assert generate_signature("Latency 12.5 ms") == "Latency <NUM> ms"

    def test_strips_uuid(self):
        message = "User 550e8400-e29b-41d4-a716-446655440000 not found"
        assert generate_signature(message) == "User <UUID> not found"

    def test_strips_iso_timestamp(self):
        message = "Failure at 2026-06-18T10:00:00Z detected"
        assert generate_signature(message) == "Failure at <TIMESTAMP> detected"

    def test_strips_ipv4_address(self):
        message = "Connection from 192.168.1.10 refused"
        assert generate_signature(message) == "Connection from <IP> refused"

    def test_strips_hex(self):
        assert generate_signature("Pointer 0xDEADBEEF freed") == "Pointer <HEX> freed"

    def test_same_signature_for_messages_differing_only_in_number(self):
        a = generate_signature("Database timeout after 20 seconds")
        b = generate_signature("Database timeout after 31 seconds")

        assert a == b == "Database timeout after <NUM> seconds"

    def test_collapses_whitespace(self):
        assert generate_signature("Disk    full   now") == "Disk full now"

    def test_handles_unicode(self):
        assert generate_signature("Café latency 9 ms") == "Café latency <NUM> ms"


class TestNormalizeLevel:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("INFO", LogLevel.INFO),
            ("information", LogLevel.INFO),
            ("WARN", LogLevel.WARN),
            ("warning", LogLevel.WARN),
            ("ERROR", LogLevel.ERROR),
            ("err", LogLevel.ERROR),
            ("CRITICAL", LogLevel.CRITICAL),
            ("fatal", LogLevel.CRITICAL),
            ("crit", LogLevel.CRITICAL),
            ("debug", LogLevel.INFO),
        ],
    )
    def test_standardizes_known_levels(self, raw, expected):
        assert normalize_level(raw) == expected

    def test_unknown_level_raises(self):
        with pytest.raises(EventValidationError):
            normalize_level("bananas")
