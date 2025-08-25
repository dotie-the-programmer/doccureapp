from django.urls import path
from .views.common_views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView,
    RegisterDoctorView,
    RegisterPatientView,
    LogoutView,
    LoginView,
    UpdateBasicUserInformationAPIView
)

app_name = "accounts"

urlpatterns = [
    # ✅ Password Reset URLs using custom views and proper namespace
    path(
        'password-reset/',
        CustomPasswordResetView.as_view(),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        CustomPasswordResetDoneView.as_view(),
        name='password_reset_done'
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm'
    ),
    path(
        'password-reset-complete/',
        CustomPasswordResetCompleteView.as_view(),
        name='password_reset_complete'
    ),


    # Other user management URLs
    path("doctor/register/", RegisterDoctorView.as_view(), name="doctor-register"),
    path("patient/register/", RegisterPatientView.as_view(), name="patient-register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", LoginView.as_view(), name="login"),
    path("update-basic-information/", UpdateBasicUserInformationAPIView.as_view(), name="update-basic-information"),
    path("doctor/login/", LoginView.as_view(), name="doctor_login"),
]
