from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from expenses.constants import PASSWORD_MISMATCH


class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="This email is already registered.")],
    )
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': PASSWORD_MISMATCH})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        # create_user() hashes the password - it is never stored or
        # returned in plain text.
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """
    simplejwt's default serializer already returns a generic
    "No active account found with the given credentials" message on failure
    (it never reveals whether the username or the password was wrong) -
    reused as-is, just wrapped in our ResponseHandler shape in the view.
    """
    pass
