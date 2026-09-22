from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from expenses.constants import EXPENSE_CREATED, SUCCESS
from expenses.filters import ExpenseFilter
from expenses.models import Expense
from expenses.serializer import ExpenseSerializer
from expenses.utils.custom_paginator import CustomPaginator
from expenses.utils.response_handler import ResponseHandler


class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPaginator
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpenseFilter

    def get_queryset(self):
        return Expense.objects.filter(owner=self.request.user).select_related('category')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        paginated = self.get_paginated_response(serializer.data)
        return ResponseHandler(data=paginated.data, message=SUCCESS, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return ResponseHandler(data=serializer.data, message=EXPENSE_CREATED, status=status.HTTP_201_CREATED)
