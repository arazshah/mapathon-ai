import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.clients.neshan.exceptions import (
    NeshanAuthenticationError,
    NeshanNotFoundError,
    NeshanRateLimitError,
    NeshanServiceError,
    NeshanValidationError,
)
from app.config import Settings

logger = logging.getLogger(__name__)


class NeshanClient:
    def __init__(
        self,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self._owns_client = http_client is None

        self.http_client = http_client or httpx.AsyncClient(
            base_url=settings.neshan_base_url.rstrip("/"),
            timeout=httpx.Timeout(settings.neshan_timeout_seconds),
            headers={
                "Api-Key": settings.neshan_api_key,
                "Accept": "application/json",
                "User-Agent": "Mapathon/0.1",
            },
        )

    async def __aenter__(self) -> "NeshanClient":
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self.http_client.aclose()

    @retry(
        retry=retry_if_exception_type(
            (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)
        ),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.3, min=0.3, max=2),
        reraise=True,
    )
    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        if not self.settings.neshan_api_key:
            raise NeshanAuthenticationError(
                "NESHAN_API_KEY در متغیرهای محیطی تنظیم نشده است."
            )

        try:
            response = await self.http_client.request(
                method=method,
                url=path,
                params=self._remove_none(params),
                json=json,
            )
        except httpx.TimeoutException as exc:
            raise NeshanServiceError(
                "زمان پاسخ‌گویی سرویس نشان به پایان رسید."
            ) from exc
        except httpx.HTTPError as exc:
            raise NeshanServiceError(
                "ارتباط با سرویس نشان برقرار نشد."
            ) from exc

        await self._raise_for_status(response)

        if response.status_code == 204:
            return {}

        try:
            body = response.json()
        except ValueError as exc:
            raise NeshanServiceError(
                "پاسخ سرویس نشان JSON معتبر نیست."
            ) from exc

        if isinstance(body, dict):
            return body

        return {"items": body}

    async def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        message = self._extract_error_message(response)

        logger.warning(
            "Neshan request failed: status=%s url=%s message=%s",
            response.status_code,
            response.request.url,
            message,
        )

        if response.status_code in {401, 403}:
            raise NeshanAuthenticationError(
                message or "کلید وب‌سرویس نشان معتبر نیست."
            )

        if response.status_code == 404:
            raise NeshanNotFoundError(
                message or "نتیجه‌ای در سرویس نشان پیدا نشد."
            )

        if response.status_code == 429:
            raise NeshanRateLimitError(
                message or "محدودیت تعداد درخواست‌های نشان رد شده است."
            )

        if response.status_code in {400, 405, 409, 422}:
            raise NeshanValidationError(
                message or "پارامترهای درخواست نشان معتبر نیستند."
            )

        raise NeshanServiceError(
            message or f"سرویس نشان خطای HTTP {response.status_code} برگرداند."
        )

    @staticmethod
    def _extract_error_message(response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return response.text[:500]

        if isinstance(data, dict):
            for key in ("message", "error", "detail", "description"):
                value = data.get(key)
                if isinstance(value, str):
                    return value

        return str(data)[:500]

    @staticmethod
    def _remove_none(
        values: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if values is None:
            return None

        return {
            key: value
            for key, value in values.items()
            if value is not None
        }
