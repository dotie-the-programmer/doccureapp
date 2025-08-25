import json
from django.urls import reverse
from datetime import datetime, timedelta
from bookings.utils import process_callback
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse


from importlib import metadata
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.http import HttpRequest, Http404, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic.base import TemplateView

from accounts.models import User
from doctors.models.general import TimeRange
from mixins.custom_mixins import PatientRequiredMixin
from .models import Booking, Payment


class BookingView(LoginRequiredMixin, View):
    template_name = "bookings/booking.html"

    def get_week_dates(self):
        """Get the next 7 days starting from today"""
        today = datetime.now().date()
        week_dates = []
        for i in range(7):
            date = today + timedelta(days=i)
            week_dates.append(
                {
                    "date": date,
                    "day": date.strftime("%a"),
                    "day_num": date.strftime("%d"),
                    "month": date.strftime("%b"),
                    "year": date.strftime("%Y"),
                    "full_date": date.strftime("%Y-%m-%d"),
                }
            )
        return week_dates

    def get_available_slots(self, doctor, date):
        """Get available time slots for a specific date"""
        day_name = date.strftime("%A").lower()
        day_schedule = getattr(doctor, day_name, None)

        if not day_schedule:
            return []

        time_slots = []
        for time_range in day_schedule.time_range.all():
            # Convert time range to slots (e.g., 30-minute intervals)
            current_time = datetime.combine(date, time_range.start)
            end_time = datetime.combine(date, time_range.end)

            while current_time < end_time:
                # Check if slot is already booked
                is_booked = doctor.appointments.filter(
                    appointment_date=date, appointment_time=current_time.time()
                ).exists()

                if not is_booked:
                    time_slots.append(
                        {
                            "time": current_time.time(),
                            "formatted_time": current_time.strftime(
                                "%I:%M %p"
                            ),
                        }
                    )
                current_time += timedelta(minutes=30)

        return time_slots

    def get(self, request: HttpRequest, *args, **kwargs):
        try:
            doctor = (
                User.objects.select_related("profile")
                .prefetch_related(
                    "sunday__time_range",
                    "monday__time_range",
                    "tuesday__time_range",
                    "wednesday__time_range",
                    "thursday__time_range",
                    "friday__time_range",
                    "saturday__time_range",
                    "appointments",
                )
                .get(
                    username=kwargs["username"],
                    role=User.RoleChoices.DOCTOR,
                    is_active=True,
                )
            )
        except User.DoesNotExist:
            raise Http404("Doctor not found")

        # Get week dates
        week_dates = self.get_week_dates()

        # Get available slots for each day
        schedule = {}
        for date_info in week_dates:
            date = datetime.strptime(date_info["full_date"], "%Y-%m-%d").date()
            schedule[date_info["full_date"]] = self.get_available_slots(
                doctor, date
            )

        context = {
            "doctor": doctor,
            "week_dates": week_dates,
            "schedule": schedule,
            "selected_date": request.GET.get(
                "date", week_dates[0]["full_date"]
            ),
        }

        return render(request, self.template_name, context)


class BookingCreateView(LoginRequiredMixin, View):
    template_name = "bookings/booking.html"

    def get(self, request: HttpRequest, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, username):
        doctor = get_object_or_404(
            User, username=username, role=User.RoleChoices.DOCTOR
        )

        # Get form data
        date = request.POST.get("selected_date")
        time = request.POST.get("selected_time")

        if not date or not time:
            messages.error(
                request, "Please select both date and time for the appointment"
            )
            return redirect("bookings:doctor-booking-view", username=username)

        try:
            # Convert string inputs to proper date/time objects
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
            appointment_time = datetime.strptime(time, "%H:%M").time()

            # Create the booking
            booking = Booking.objects.create(
                doctor=doctor,
                patient=request.user,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            )

            # Redirect to payment page instead
            return redirect("bookings:booking-payment", booking_id=booking.id)


        except ValueError:
            messages.error(request, "Invalid date or time format")
        except Exception as e:
            messages.error(request, str(e))

        return redirect("bookings:doctor-booking-view", username=username)


class BookingSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "bookings/booking-success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["booking"] = Booking.objects.get(id=kwargs["booking_id"])
        return context


class BookingInvoiceView(LoginRequiredMixin, TemplateView):
    template_name = "bookings/booking-invoice.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        booking = get_object_or_404(
            Booking.objects.select_related(
                "doctor", "doctor__profile", "patient", "patient__profile"
            ),
            id=kwargs["booking_id"],
        )

        # Ensure user can only view their own bookings
        if not (
            self.request.user == booking.patient
            or self.request.user == booking.doctor
        ):
            raise Http404("Not found")

        context["booking"] = booking
        context["issued_date"] = booking.booking_date.strftime("%d/%m/%Y")

        # Calculate invoice amounts
        consultation_fee = booking.doctor.profile.price_per_consultation
        context["subtotal"] = consultation_fee
        context["total"] = (
            consultation_fee  # Add any additional fees/discounts here
        )

        return context

class BookingPaymentView(LoginRequiredMixin, View):
    template_name = "bookings/booking-payment.html"

    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)

        context = {
            "booking": booking,
            "phone": getattr(request.user, "phone_number", ""),
            "amount": booking.doctor.profile.price_per_consultation,
        }
        return render(request, self.template_name, context)

    def post(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        phone = request.POST.get("phone")
        amount = 1  # test amount

        from bookings.credentials import MpesaAccessToken, LipanaMpesaPpassword
        import requests, json

        access_token = MpesaAccessToken.generate_access_token()
        decode_password, lipa_time = LipanaMpesaPpassword.generate_password()

        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        call_back_url = f"https://8f8264a36109.ngrok-free.app/bookings/mpesa/callback/"
        payload = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": decode_password,
            "Timestamp": lipa_time,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(float(amount)),
            "PartyA": phone,
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            "PhoneNumber": phone,
            "CallBackURL": call_back_url,
            "AccountReference": "Doccure",
            "TransactionDesc": "Doctor Appointment",
        }

        response = requests.post(api_url, json=payload, headers=headers)
        try:
            data = response.json()
            if data.get("ResponseCode") == "0":
                payment = Payment.objects.create(
                    booking=booking,
                    status="pending",
                    phone_number=phone,
                    amount=amount,
                    checkout_id=data["CheckoutRequestID"],
                )

                # ✅ If AJAX → return JSON
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({
                        "status": "pending",
                        "payment_id": payment.id,
                        "message": "prompt sent! please Check your phone."
                    })

                # ✅ Otherwise → normal Django flow
                messages.success(request, "✅ Your number has been propmted,please make payment.")
                return redirect("bookings:booking-success", booking_id=booking.id)

            else:
                error_msg = data.get("ResponseDescription", "Unknown error")
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"status": "failed", "message": error_msg}, status=400)

                messages.error(request, f"❌ Payment initiation failed: {error_msg}")
                return render(request, self.template_name, {"booking": booking, "phone": phone, "amount": amount})

        except Exception as e:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

            messages.error(request, f"Input phone number with the correct format: {str(e)}")
            return render(request, self.template_name, {"booking": booking, "phone": phone, "amount": amount})
@require_GET
def check_payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return JsonResponse({
        "success": payment.status == "success",
        "status": payment.status
    })

@csrf_exempt
def mpesa_callback(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print("M-Pesa Callback Data:", data)

            # Extract CheckoutID and result
            body = data.get("Body", {}).get("stkCallback", {})
            checkout_id = body.get("CheckoutRequestID")
            result_code = body.get("ResultCode")
            result_desc = body.get("ResultDesc")

            # Find the payment linked to this checkout
            payment = Payment.objects.filter(checkout_id=checkout_id).first()

            if not payment:
                return JsonResponse({"ResultCode": 1, "ResultDesc": "Payment not found"})

            # Update payment based on M-Pesa response
            if result_code == 0:
                # Success: extract metadata
                metadata = body.get("CallbackMetadata", {}).get("Item", [])
                mpesa_receipt = next((item["Value"] for item in metadata if item["Name"] == "MpesaReceiptNumber"), None)
                phone_number = next((item["Value"] for item in metadata if item["Name"] == "PhoneNumber"), None)
                name = next((item["Value"] for item in metadata if item["Name"] == "Name"), None)

                payment.transaction_id = mpesa_receipt
                payment.phone_number = phone_number or payment.phone_number
                payment.mpesa_name = name
                payment.status = "successful"
                payment.save()

            else:
                payment.status = "failed"
                payment.description = result_desc
                payment.save()

            return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback processed successfully"})

        except Exception as e:
            return JsonResponse({"ResultCode": 1, "ResultDesc": str(e)})

    return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request"})

def confirm_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    payment = Payment.objects.filter(booking=booking).last()

    return render(request, "confirm_payment.html", {
        "booking": booking,
        "payment": payment,
    })


def payment_status(request, checkout_id):
    try:
        payment = Payment.objects.get(checkout_id=checkout_id)
        return JsonResponse({"status": payment.status, "transaction_id": payment.transaction_id})
    except Payment.DoesNotExist:
        return JsonResponse({"status": "not_found"})






