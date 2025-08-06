from datetime import timedelta

from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, UntypedToken
from rest_framework_simplejwt.views import TokenObtainPairView

from app_auth.serializers import (
    ForgotPasswordSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    OTPRegisterSerializer,
    RegisterSerializer,
    RequestOTPSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    ValidateOTPSerializer,
)
from app_email.services import EmailService

from .models import OTP

User = get_user_model()


class IsSuperUser(IsAdminUser):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class LoginView(TokenObtainPairView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=LoginResponseSerializer,
                description="Successfully authenticated",
            )
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except TokenError as exc:
            raise ValidationError("Invalid token") from exc


class ForgotPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(email=request.data["email"])
        except User.DoesNotExist as exc:
            raise ValidationError("User with this email does not exist") from exc

        token = AccessToken.for_user(user)
        token.set_exp(lifetime=timedelta(minutes=15))
        reset_password_link = f"{request.data["reset_url"]}?token={str(token)}"

        EmailService.send_password_reset(request.data["email"], reset_password_link)
        return Response({"message": "Password reset email sent successfully"})


class ResetPasswordAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = request.data["token"]
        new_password = request.data["new_password"]

        try:
            decoded_token = UntypedToken(token)
            user = User.objects.get(id=decoded_token["user_id"])
            user.set_password(new_password)
            user.save()

            return Response({"message": "Password updated successfully"})
        except (TokenError, User.DoesNotExist) as exc:
            raise ValidationError("Invalid or expired reset token") from exc


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        assert isinstance(serializer.validated_data, dict)
        user = User.objects.create_user(
            username=serializer.validated_data["email"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return Response({"message": "User registered successfully", "data": user.email})


class UserView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]


# OTP related views


class RequestRegisterOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RequestOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data["email"]
        otp = OTP.generate_otp(email)

        # Send OTP via email
        EmailService.send_email(
            subject="Your OTP Code",
            recipients=[email],
            template_name="emails/otp.html",
            context={"otp": otp},
        )

        return Response({"message": "OTP sent successfully"})


class ValidateRegisterOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = OTPRegisterSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(email=request.data["email"])
        if user:
            raise ValidationError({"email": "Already registered, please login"})

        # Create user
        # If you want to store additional fields, you should create the profile model with the required fields and create the profile after user is created
        user = User.objects.create_user(
            username=request.data["email"],
            email=request.data["email"],
            first_name=request.data["first_name"],
            last_name=request.data["last_name"],
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class RequestLoginOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RequestOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data["email"]
        user = User.objects.get(email=email)
        if not user:
            raise ValidationError({"email": "User with this email is not registered"})

        otp = OTP.generate_otp(email)

        # Send OTP via email
        EmailService.send_email(
            subject="Your OTP Code",
            recipients=[email],
            template_name="emails/otp.html",
            context={"otp": otp},
        )

        return Response({"message": "OTP sent successfully"})


class ValidateLoginOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ValidateOTPSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data["email"]
        otp = request.data["otp"]

        if not OTP.validate_otp(email, otp):
            raise ValidationError({"otp": "Invalid or expired OTP"})

        # Generate JWT tokens
        try:
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": UserSerializer(user).data,
                }
            )
        except User.DoesNotExist:
            return Response({"message": "OTP validated successfully"})
