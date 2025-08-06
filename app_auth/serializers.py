import random
import string

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app_auth.models import OTP

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password"]


class LoginResponseSerializer(serializers.ModelSerializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

    class Meta:
        model = User
        fields = ["access", "refresh", "user"]


class LoginSerializer(TokenObtainPairSerializer):
    def create(self, validated_data):
        return validated_data

    def update(self, instance, validated_data):
        return instance


class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        error_messages={"min_length": "Password must be at least 8 characters long"},
    )

    class Meta:
        model = User
        fields = ["old_password", "new_password"]

    def validate(self, attrs):
        user = self.context["request"].user
        if not authenticate(username=user.username, password=attrs["old_password"]):
            raise ValidationError({"old_password": "Current password is incorrect"})
        return attrs


class ForgotPasswordSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email address is required",
            "invalid": "Please enter a valid email address",
        },
    )
    reset_url = serializers.URLField(
        required=True,
        error_messages={
            "required": "Reset URL is required",
            "invalid": "Please enter a valid URL",
        },
    )

    class Meta:
        model = User
        fields = ["email", "reset_url"]


class ResetPasswordSerializer(serializers.ModelSerializer):
    token = serializers.CharField(
        required=True, error_messages={"required": "Reset token is required"}
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        error_messages={
            "required": "New password is required",
            "min_length": "Password must be at least 8 characters long",
        },
    )

    class Meta:
        model = User
        fields = ["token", "new_password"]


class LogoutSerializer(serializers.ModelSerializer):
    refresh = serializers.CharField(
        required=True, error_messages={"required": "Refresh token is required"}
    )

    class Meta:
        model = User
        fields = ["refresh"]


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(characters) for _ in range(length))


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def create(self, validated_data):
        password = generate_random_password()
        user = User.objects.create_user(**validated_data, password=password)
        return user


class RequestOTPSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email address is required",
            "invalid": "Please enter a valid email address",
        },
    )

    class Meta:
        model = OTP
        fields = ["email"]


class ValidateOTPSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email address is required",
            "invalid": "Please enter a valid email address",
        },
    )
    otp = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        error_messages={
            "required": "OTP is required",
            "min_length": "OTP must be 6 digits",
            "max_length": "OTP must be 6 digits",
        },
    )

    class Meta:
        model = OTP
        fields = ["email", "otp"]


class OTPRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email address is required",
            "invalid": "Please enter a valid email address",
        },
    )
    otp = serializers.CharField(
        required=True,
        min_length=6,
        max_length=6,
        error_messages={
            "required": "OTP is required",
            "min_length": "OTP must be 6 digits",
            "max_length": "OTP must be 6 digits",
        },
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "otp"]

    def validate(self, attrs):
        if not OTP.validate_otp(attrs["email"], attrs["otp"]):
            raise serializers.ValidationError({"otp": "Invalid or expired OTP"})
        return attrs
