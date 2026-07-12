from __future__ import annotations

import asyncio
import math
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse


class InMemoryRateLimitMiddleware:
    """
    Rate limiter داخل حافظه برای یک Process.

    این نسخه برای یک Worker مناسب است.
    برای چند Worker یا چند Replica باید از Redis استفاده شود.
    """

    def __init__(
        self,
        app: Callable[..., Awaitable[Any]],
        *,
        limit: int = 10,
        window_seconds: int = 60,
        protected_path: str = "/api/v1/query",
        enabled: bool = True,
    ) -> None:
        self.app = app
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self.protected_path = protected_path
        self.enabled = enabled

        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    @staticmethod
    def _client_key(request: Request) -> str:
        if request.client and request.client.host:
            return request.client.host

        return "unknown"

    async def _check_limit(self, key: str) -> tuple[bool, int, int]:
        now = time.monotonic()
        window_start = now - self.window_seconds

        async with self._lock:
            timestamps = self._requests[key]

            while timestamps and timestamps[0] <= window_start:
                timestamps.popleft()

            if len(timestamps) >= self.limit:
                retry_after = self.window_seconds

                if timestamps:
                    retry_after = max(
                        1,
                        math.ceil(
                            self.window_seconds - (now - timestamps[0])
                        ),
                    )

                return False, 0, retry_after

            timestamps.append(now)

            remaining = max(0, self.limit - len(timestamps))
            return True, remaining, self.window_seconds

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[Any]],
    ) -> None:
        if not self.enabled or scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        should_limit = (
            request.method.upper() == "POST"
            and request.url.path == self.protected_path
        )

        if not should_limit:
            await self.app(scope, receive, send)
            return

        client_key = self._client_key(request)
        allowed, remaining, retry_after = await self._check_limit(client_key)

        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "rate_limit_exceeded",
                    "message": (
                        "تعداد درخواست‌ها بیش از حد مجاز است. "
                        "لطفاً کمی بعد دوباره تلاش کنید."
                    ),
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

            await response(scope, receive, send)
            return

        async def send_with_headers(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (
                            b"x-ratelimit-limit",
                            str(self.limit).encode("ascii"),
                        ),
                        (
                            b"x-ratelimit-remaining",
                            str(remaining).encode("ascii"),
                        ),
                        (
                            b"x-ratelimit-reset",
                            str(retry_after).encode("ascii"),
                        ),
                    ]
                )
                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_headers)
