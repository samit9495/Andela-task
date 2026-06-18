"""HTTP middleware for the API layer."""

from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

_RequestHandler = Callable[[Request], Awaitable[Response]]


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose declared body exceeds ``max_bytes`` with a 413."""

    def __init__(self, app: object, max_bytes: int) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: _RequestHandler) -> Response:
        content_length = request.headers.get("content-length")
        if (
            content_length is not None
            and content_length.isdigit()
            and int(content_length) > self._max_bytes
        ):
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large", "code": "payload_too_large"},
            )
        return await call_next(request)
