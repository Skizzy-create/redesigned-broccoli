from __future__ import annotations

from fastapi import status


class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "not_found") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "conflict") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_409_CONFLICT)


class ValidationError(AppError):
    def __init__(self, message: str, code: str = "validation_error") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class PayloadTooLargeError(AppError):
    def __init__(self, message: str, code: str = "payload_too_large") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)


class UnsupportedMediaTypeError(AppError):
    def __init__(self, message: str, code: str = "unsupported_media_type") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str, code: str = "service_unavailable") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class TooManyRequestsError(AppError):
    def __init__(self, message: str, code: str = "too_many_requests") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class DocumentProcessingError(AppError):
    def __init__(self, message: str, code: str = "document_processing_failed") -> None:
        super().__init__(message=message, code=code, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
