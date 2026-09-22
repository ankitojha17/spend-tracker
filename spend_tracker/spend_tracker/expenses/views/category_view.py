from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from expenses.constants import CATEGORY_CREATED, SUCCESS
from expenses.models import Category
from expenses.serializer import CategorySerializer
from expenses.utils.response_handler import ResponseHandler


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return ResponseHandler(data=serializer.data, message=SUCCESS, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return ResponseHandler(data=serializer.data, message=CATEGORY_CREATED, status=status.HTTP_201_CREATED)
