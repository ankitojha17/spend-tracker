from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidMonthFormatError(APIException):
    """Raised when the `month` query param on /summary isn't YYYY-MM."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "month must be in YYYY-MM format."
    default_code = 'invalid_month_format'
