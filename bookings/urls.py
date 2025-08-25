from django.urls import path

from . import views
from .views import (
    BookingView,
    BookingCreateView,
    BookingSuccessView,
    BookingInvoiceView,
    BookingPaymentView,
    mpesa_callback,

)

app_name = "bookings"

urlpatterns = [
    path(
        "doctor/<slug:username>",
        BookingView.as_view(),
        name="doctor-booking-view",
    ),
    path(
        "create/<str:username>/",
        BookingCreateView.as_view(),
        name="create-booking",
    ),
    path(
        "<int:booking_id>/success/",
        BookingSuccessView.as_view(),
        name="booking-success",
    ),
    path(
        "<int:booking_id>/invoice/",
        BookingInvoiceView.as_view(),
        name="booking-invoice",
    ),

    path("confirm-payment/", views.confirm_payment, name="confirm_payment"),

    path(
    "pay/<int:booking_id>/",
    BookingPaymentView.as_view(),
    name="booking-payment"
   ),

    path(
        "mpesa/callback/",
         mpesa_callback,
        name="mpesa_callback"),
    
    


]
