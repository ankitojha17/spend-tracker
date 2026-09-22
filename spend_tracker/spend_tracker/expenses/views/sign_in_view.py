from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from expenses.constants import LOGIN_SUCCESS
from expenses.serializer import LoginSerializer
from expenses.utils.response_handler import ResponseHandler
from expenses.utils.throttles import LoginRateThrottle


class SignInView(TokenObtainPairView):
    """
    Thin wrapper around simplejwt's TokenObtainPairView so a successful
    login returns our standard { success, message, data } shape instead of
    simplejwt's bare { access, refresh }. Invalid credentials raise
    AuthenticationFailed, which the global exception handler already
    formats consistently - nothing extra needed here for the failure path.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return ResponseHandler(data=serializer.validated_data, message=LOGIN_SUCCESS, status=status.HTTP_200_OK)
