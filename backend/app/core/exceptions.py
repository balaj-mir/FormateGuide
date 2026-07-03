"""
FormatGuard Exception Handlers — centralized error handling for all API responses.
Maps all custom HTTP errors to consistent JSON response format.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

logger = structlog.get_logger()


class FormatGuardException(Exception):
    """Base exception for FormatGuard-specific errors."""

    def __init__(self, status_code: int, detail: str, error_code: str | None = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class FileValidationError(FormatGuardException):
    """Raised when uploaded file fails validation (wrong type, too large)."""

    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail, error_code="FILE_VALIDATION_ERROR")


class QuotaExceededError(FormatGuardException):
    """Raised when user exceeds monthly check quota."""

    def __init__(self, tier: str, limit: int):
        detail = (
            f"Monthly check quota exceeded. Your '{tier}' plan allows {limit} checks/month. "
            f"Upgrade your plan at /settings for more checks."
        )
        super().__init__(status_code=402, detail=detail, error_code="QUOTA_EXCEEDED")


class InvalidRulesetError(FormatGuardException):
    """Raised when ruleset JSON schema is invalid."""

    def __init__(self, detail: str = "Invalid ruleset JSON schema"):
        super().__init__(status_code=422, detail=detail, error_code="INVALID_RULESET")


class RateLimitExceededError(FormatGuardException):
    """Raised when user exceeds rate limit."""

    def __init__(self):
        super().__init__(
            status_code=429,
            detail="Rate limit exceeded. Please wait before uploading again.",
            error_code="RATE_LIMITED",
        )


class ProcessingServiceError(FormatGuardException):
    """Raised when document processing service is unavailable."""

    def __init__(self):
        super().__init__(
            status_code=503,
            detail="Document processing service is temporarily unavailable. Please try again later.",
            error_code="SERVICE_UNAVAILABLE",
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""

    @app.exception_handler(FormatGuardException)
    async def formatguard_exception_handler(
        request: Request, exc: FormatGuardException
    ) -> JSONResponse:
        logger.warning(
            "FormatGuard error",
            status_code=exc.status_code,
            detail=exc.detail,
            error_code=exc.error_code,
            path=str(request.url),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " → ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "details": errors,
                "status_code": 422,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=str(request.url),
        )
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "An unexpected error occurred. Our team has been notified.",
                "status_code": 500,
            },
        )
