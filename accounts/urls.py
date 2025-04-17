from django.urls import path, include
from .views.common_views import *
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    # Password Reset URLs with Custom Templates
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='auth/password_reset.html',
            success_url='/accounts/password-reset/done/'  # Add success_url here
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='auth/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='auth/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='auth/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # Authentication & User Management URLs
    path("doctor/register/", RegisterDoctorView.as_view(), name="doctor-register"),
    path("patient/register/", RegisterPatientView.as_view(), name="patient-register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", LoginView.as_view(), name="login"),
    path("update-basic-information/", UpdateBasicUserInformationAPIView.as_view(), name="update-basic-information"),

    # Added doctor login URL pattern
    path("doctor/login/", LoginView.as_view(), name="doctor_login"),

]
