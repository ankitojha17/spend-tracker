import logging

from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.views import exception_handler as drf_exception_handler

from expenses.constants import GENERIC_ERROR, VALIDATION_FAILED
from expenses.utils.response_handler import ResponseHandler

logger = logging.getLogger(__name__)


def global_exception_handler(exc, context):
    """
    Single place that turns every exception DRF can raise into our
    standard { success, message, errors } shape, instead of each view
    having to know how to format its own errors.
    """
    # Field-level validation errors keep their per-field detail so the
    # frontend can show "amount: Amount must be greater than 0." etc.
    if isinstance(exc, ValidationError):
        return ResponseHandler(
            success=False,
            message=VALIDATION_FAILED,
            errors=exc.detail,
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return ResponseHandler(success=False, message=str(exc), status=status.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, PermissionDenied):
        return ResponseHandler(success=False, message=str(exc), status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, NotFound):
        return ResponseHandler(success=False, message=str(exc), status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, Throttled):
        wait_message = f" Try again in {exc.wait} seconds." if exc.wait else ""
        return ResponseHandler(
            success=False,
            message=f"Too many requests.{wait_message}",
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # Anything else DRF already knows how to turn into a Response
    # (e.g. MethodNotAllowed, UnsupportedMediaType) - reuse its status
    # code but still wrap it in our shape for consistency.
    response = drf_exception_handler(exc, context)
    if response is not None:
        return ResponseHandler(success=False, message=str(exc), status=response.status_code)

    # Anything unhandled is a genuine bug - log the real exception for
    # debugging, but never leak internals to the client.
    logger.exception("Unhandled exception in request", exc_info=exc)
    return ResponseHandler(
        success=False,
        message=GENERIC_ERROR,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
