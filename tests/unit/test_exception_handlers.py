"""Unit tests for the global exception handlers."""

import asyncio
import json

from backend.app.core.exceptions import DomainError, IncidentNotFound
from backend.app.main import handle_domain_error, handle_unexpected
from starlette.requests import Request


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/x",
            "raw_path": b"/x",
            "query_string": b"",
            "headers": [],
            "scheme": "http",
            "server": ("test", 80),
        }
    )


class TestExceptionHandlers:
    def test_domain_handler_maps_incident_not_found_to_404(self):
        response = asyncio.run(handle_domain_error(_request(), IncidentNotFound("nope")))
        body = json.loads(response.body)

        assert response.status_code == 404
        assert body["code"] == "incident_not_found"

    def test_domain_handler_defaults_to_400(self):
        response = asyncio.run(handle_domain_error(_request(), DomainError("generic")))

        assert response.status_code == 400

    def test_unexpected_handler_is_sanitized(self):
        response = asyncio.run(handle_unexpected(_request(), ValueError("secret /etc/passwd leak")))
        body = json.loads(response.body)

        assert response.status_code == 500
        assert body == {"detail": "Internal server error", "code": "internal_error"}
