from django.contrib import admin
from django.urls import path

from .views import (
    ForgotPasswordAPIView,
    LoginView,
    LogoutView,
    RegisterView,
    RequestLoginOTPView,
    RequestRegisterOTPView,
    ResetPasswordAPIView,
    ValidateLoginOTPView,
    ValidateRegisterOTPView,
)

# Auth related URLs
# you should comment out the urls that you don't need below
urlpatterns = [
    # for username/password based login/register
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("forgot-password/", ForgotPasswordAPIView.as_view(), name="forgot-password"),
    path("reset-password/", ResetPasswordAPIView.as_view(), name="reset-password"),
    # for OTP based login/register
    path("request/login/otp/", RequestLoginOTPView.as_view(), name="request-login-otp"),
    path("login/otp/", ValidateLoginOTPView.as_view(), name="validate-login-otp"),
    path(
        "request/register/otp/",
        RequestRegisterOTPView.as_view(),
        name="request-register-otp",
    ),
    path("register/otp/", ValidateRegisterOTPView.as_view(), name="register-otp"),
]
