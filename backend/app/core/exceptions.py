from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base exception for all domain and application errors."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    """Raised when an entity or resource is not found."""
    def __init__(self, resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details or {"resource": resource, "identifier": str(identifier)},
        )


class ConflictError(AppException):
    """Raised on uniqueness violations or conflicting state transitions."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class AuthenticationError(AppException):
    """Raised on invalid credentials or expired sessions."""
    def __init__(self, message: str = "Invalid credentials or expired session"):
        super().__init__(
            message=message,
            code="UNAUTHENTICATED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class PermissionDeniedError(AppException):
    """Raised when an authenticated user lacks required role/privileges."""
    def __init__(self, message: str = "Permission denied for this resource"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationError(AppException):
    """Raised on invalid input or constraint violation."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Unified FastAPI exception handler formatting all domain errors consistently."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )
