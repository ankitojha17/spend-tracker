from rest_framework import generics, status
from rest_framework.permissions import AllowAny

from expenses.constants import ACCOUNT_CREATED
from expenses.serializer import SignUpSerializer
from expenses.utils.response_handler import ResponseHandler


class SignUpView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = {'id': user.id, 'username': user.username, 'email': user.email}
        return ResponseHandler(data=data, message=ACCOUNT_CREATED, status=status.HTTP_201_CREATED)
