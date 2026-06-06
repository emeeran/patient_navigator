"""Custom application exceptions with FastAPI exception handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message


class InvalidCredentialsError(AppException):
    status_code = 401
    error_code = "invalid_credentials"
    message = "Invalid email or password"


class AccountDisabledError(AppException):
    status_code = 403
    error_code = "account_disabled"
    message = "Account has been disabled"


class TokenExpiredError(AppException):
    status_code = 401
    error_code = "token_expired"
    message = "Token has expired"


class InvalidTokenError(AppException):
    status_code = 401
    error_code = "invalid_token"
    message = "Invalid token"


class MissingAuthenticationError(AppException):
    status_code = 401
    error_code = "missing_authentication"
    message = "Authentication required"


class InsufficientPermissionsError(AppException):
    status_code = 403
    error_code = "insufficient_permissions"
    message = "You do not have permission to perform this action"


class DuplicateEmailError(AppException):
    status_code = 409
    error_code = "email_already_registered"
    message = "A user with this email already exists"


class TokenReuseDetectedError(AppException):
    status_code = 401
    error_code = "security.token_reuse_detected"
    message = "Token reuse detected. All sessions have been invalidated."


class RateLimitExceededError(AppException):
    status_code = 429
    error_code = "rate_limit_exceeded"
    message = "Too many failed login attempts"


class NotFoundError(AppException):
    status_code = 404
    error_code = "not_found"
    message = "Resource not found"


class ValidationError(AppException):
    status_code = 422
    error_code = "validation_error"
    message = "Validation failed"


class InvalidStateTransitionError(AppException):
    status_code = 422
    error_code = "invalid_state_transition"
    message = "Invalid status transition"


class ArchivedPatientError(AppException):
    status_code = 400
    error_code = "archived_patient"
    message = "Cannot modify an archived patient"


class FileTooLargeError(AppException):
    status_code = 413
    error_code = "file_too_large"
    message = "File exceeds maximum allowed size"


class InvalidFileTypeError(AppException):
    status_code = 422
    error_code = "invalid_file_type"
    message = "File type not supported"


class MIMEMismatchError(AppException):
    status_code = 422
    error_code = "mime_mismatch"
    message = "File content does not match declared MIME type"


class CompletedFollowUpError(AppException):
    status_code = 400
    error_code = "followup_already_completed"
    message = "Completed follow-ups cannot be modified"


class ConflictError(AppException):
    status_code = 409
    error_code = "conflict"
    message = "Resource already exists"


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Format AppException as RFC 9457 Problem Details JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": exc.error_code,
            "status": exc.status_code,
            "detail": exc.message,
            "error_code": exc.error_code,
        },
    )


def register_exception_handlers(app):
    """Register all custom exception handlers on the FastAPI app."""
    for exc_class in [
        InvalidCredentialsError,
        AccountDisabledError,
        TokenExpiredError,
        InvalidTokenError,
        MissingAuthenticationError,
        InsufficientPermissionsError,
        DuplicateEmailError,
        TokenReuseDetectedError,
        RateLimitExceededError,
        NotFoundError,
        ValidationError,
        InvalidStateTransitionError,
        ArchivedPatientError,
        FileTooLargeError,
        InvalidFileTypeError,
        MIMEMismatchError,
        CompletedFollowUpError,
        ConflictError,
    ]:
        app.add_exception_handler(exc_class, app_exception_handler)  # type: ignore[arg-type]
