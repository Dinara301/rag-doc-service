from starlette.datastructures import Headers
from starlette.status import HTTP_413_CONTENT_TOO_LARGE
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.errors import error_response


class RequestSizeLimitMiddleware:
    """Reject requests whose declared `Content-Length` exceeds a limit, before reading the body.

    FastAPI parses multipart uploads before a route runs, so a check inside the route would come
    after the whole body was received and spooled. Requests without `Content-Length` (chunked)
    pass through and are still bounded by the per-file read limit in the upload route; a proxy
    limit is added at deployment.
    """

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        """Wrap `app`, allowing request bodies of at most `max_bytes`."""
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Answer 413 for oversized declared bodies; otherwise call the wrapped app."""
        if scope["type"] == "http":
            declared = Headers(scope=scope).get("content-length")
            if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
                response = error_response(
                    HTTP_413_CONTENT_TOO_LARGE,
                    f"Request body exceeds the {self.max_bytes} byte limit",
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
