from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenRefreshView

from expenses.constants import TOKEN_REFRESHED
from expenses.utils.response_handler import ResponseHandler


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            # A malformed/expired/blacklisted refresh token raises simplejwt's
            # own TokenError, which isn't an APIException DRF's exception
            # handler recognises - convert it the same way simplejwt's base
            # view does, so it comes back as a clean 401 instead of a 500.
            raise InvalidToken(e.args[0])
        return ResponseHandler(data=serializer.validated_data, message=TOKEN_REFRESHED, status=status.HTTP_200_OK)
