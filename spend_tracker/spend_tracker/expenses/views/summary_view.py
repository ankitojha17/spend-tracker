from datetime import datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from expenses.constants import SUCCESS
from expenses.services import calculate_summary
from expenses.utils.exceptions import InvalidMonthFormatError
from expenses.utils.response_handler import ResponseHandler


class SummaryView(APIView):
    """
    GET /api/summary?month=YYYY-MM

    month defaults to the current calendar month when omitted. All the
    actual calculation (totals, per-category breakdown, month-over-month
    change, >20% insights) lives in services.calculate_summary so it stays
    unit-testable without going through HTTP/auth.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        month_param = request.query_params.get('month')
        if month_param:
            try:
                parsed = datetime.strptime(month_param, '%Y-%m')
            except ValueError:
                raise InvalidMonthFormatError()
            year, month = parsed.year, parsed.month
        else:
            today = datetime.today()
            year, month = today.year, today.month

        data = calculate_summary(request.user, year, month)
        return ResponseHandler(data=data, message=SUCCESS, status=status.HTTP_200_OK)
