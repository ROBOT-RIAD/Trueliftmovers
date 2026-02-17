from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking



@shared_task
def send_booking_email(booking_id):
    try:
        booking = Booking.objects.select_related("user").get(id=booking_id)

        # ------------------------
        # USER EMAIL
        # ------------------------
        subject = "Booking Created Successfully"
        message = f"""
Hello {booking.user.profile.full_name},

Your booking has been created successfully.

Pickup Address: {booking.pickup_address}
Drop Address: {booking.drop_off_address}
Initial Price: {booking.initial_price}

Thank you.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[booking.user.email],
        )

        return f"Booking notification processed {booking.id}"

    except Booking.DoesNotExist:
        return "Booking not found"
