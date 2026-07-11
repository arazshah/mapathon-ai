import uuid

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from app.clients.neshan.exceptions import (
    NeshanAuthenticationError,
    NeshanError,
    NeshanNotFoundError,
    NeshanRateLimitError,
    NeshanServiceError,
    NeshanValidationError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NeshanAuthenticationError)
    async def neshan_authentication_handler(
        request: Request,
        exc: NeshanAuthenticationError,
    ) -> ORJSONResponse:
        return _response(502, str(exc))

    @app.exception_handler(NeshanRateLimitError)
    async def neshan_rate_limit_handler(
        request: Request,
        exc: NeshanRateLimitError,
    ) -> ORJSONResponse:
        return _response(429, str(exc))

    @app.exception_handler(NeshanNotFoundError)
    async def neshan_not_found_handler(
        request: Request,
        exc: NeshanNotFoundError,
    ) -> ORJSONResponse:
        return _response(404, str(exc))

    @app.exception_handler(NeshanValidationError)
    async def neshan_validation_handler(
        request: Request,
        exc: NeshanValidationError,
    ) -> ORJSONResponse:
        return _response(422, str(exc))

    @app.exception_handler(NeshanServiceError)
    async def neshan_service_handler(
        request: Request,
        exc: NeshanServiceError,
    ) -> ORJSONResponse:
        return _response(502, str(exc))

    @app.exception_handler(NeshanError)
    async def neshan_fallback_handler(
        request: Request,
        exc: NeshanError,
    ) -> ORJSONResponse:
        return _response(502, str(exc))


def _response(status_code: int, message: str) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": "neshan_service_error",
            "message": message,
            "request_id": str(uuid.uuid4()),
        },
    )
