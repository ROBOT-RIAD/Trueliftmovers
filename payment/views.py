from django.shortcuts import render
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from accounts.response import success_response
import stripe
from .models import Booking, Payment
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from .serializers import CheckoutSessionSerializer,PaymentSuccessSerializer,PaymentDetailSerializer
from notifications.tasks import create_notification_task

stripe.api_key=settings.STRIPE_SECRET_KEY


def custom_error_response(error_type, message, status_code=status.HTTP_400_BAD_REQUEST):
    return {
        "success": False,
        "error": {
            "type": error_type,
            "message": message
        }
    }, status_code


# Create your views here.

class CreateCheckoutSessionView(APIView):
    @swagger_auto_schema(
        operation_summary="Create Stripe Checkout Session",
        operation_description="Create a checkout session for truck or movers payment.",
        request_body=CheckoutSessionSerializer,
        tags=['Payments']
    )
    def post(self, request, *args, **kwargs):
        booking_id = request.data.get('booking_id')
        payment_type = request.data.get('type_payment')  # 'truck' or 'mover'

        if payment_type not in ['truck', 'mover']:
            response, code = custom_error_response("ValidationError", "Invalid payment type")
            return Response(response, status=code)

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            response, code = custom_error_response("NotFound", "Booking not found")
            return Response(response, status=code)

        # Prevent paying movers before truck
        if payment_type == 'mover' and not booking.truck_payment_status:
            response, code = custom_error_response("ValidationError", "Truck payment must be completed first")
            return Response(response, status=code)

        try:
            with transaction.atomic():
                payment, created = Payment.objects.get_or_create(
                    booking=booking,
                    type_payment=payment_type,
                    defaults={
                        'amount': booking.final_price if payment_type == 'truck' else booking.movers_total,
                        'currency': 'usd',
                        'status': 'pending'
                    }
                )

                # Create Stripe checkout session
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': payment.currency,
                            'product_data': {
                                'name': f'Booking #{booking.id} - {payment_type.capitalize()} Payment',
                            },
                            'unit_amount': int(payment.amount * 100),
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    customer_email=booking.user.email,
                    success_url=request.build_absolute_uri('/payment/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                    cancel_url=request.build_absolute_uri('/payment/cancel/'),
                    metadata={'payment_id': payment.id}
                )

                payment.stripe_payment_intent_id = session.payment_intent
                payment.save()

            return success_response(f"{payment_type.capitalize()} payment session created", data={'checkout_url': session.url})
        
        except stripe.error.StripeError as e:
            response, code = custom_error_response("StripeError", str(e))
            return Response(response, status=code)

        except Exception as e:
            response, code = custom_error_response("ServerError", str(e))
            return Response(response, status=code)
        



class PaymentSuccessView(APIView):
    @swagger_auto_schema(
        operation_summary="Handle Stripe Payment Success",
        operation_description="Verify Stripe session, update payment and booking status.",
        request_body=PaymentSuccessSerializer,
        tags=['Payments']
    )
    def post(self, request):

        session_id = request.data.get('session_id')

        if not session_id:
            response, code = custom_error_response(
                "ValidationError",
                "Session ID not provided"
            )
            return Response(response, status=code)

        try:
            session = stripe.checkout.Session.retrieve(session_id)

            if not session or session.payment_status != "paid":
                response, code = custom_error_response(
                    "ValidationError",
                    "Payment not completed or invalid session"
                )
                return Response(response, status=code)

            payment_intent = stripe.PaymentIntent.retrieve(
                session.payment_intent
            )

            payment_id = session.metadata.get('payment_id')

            if not payment_id:
                response, code = custom_error_response(
                    "ValidationError",
                    "Payment ID missing in Stripe metadata"
                )
                return Response(response, status=code)

            payment = Payment.objects.get(id=payment_id)


            if payment.is_paid:
                return success_response(
                    "Payment already recorded"
                )

            with transaction.atomic():

                payment.status = 'succeeded'
                payment.is_paid = True
                payment.paid_at = timezone.now()

                payment.stripe_payment_intent_id = payment_intent.id
                payment.stripe_payment_method_id = payment_intent.payment_method

                payment.save()

                booking = payment.booking

                if payment.type_payment == 'truck':
                    booking.truck_payment_status = True
                    booking.status = "accepted"
                else:
                    booking.mover_payment_status = True
                    booking.status = "complete"

                booking.save()

            create_notification_task.delay(
                user_id=booking.user.id,
                title="Payment Successful",
                body=f"Your {payment.type_payment} payment was completed successfully.",
                data={
                    "booking_id": booking.id,
                    "payment_id": payment.id,
                    "amount": float(payment.amount),
                    "payment_type": payment.type_payment,
                    "status": payment.status,
                    "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                },
                broadcast_user=False,
                broadcast_admin=True
            )

            serializer = PaymentDetailSerializer(payment)

            return success_response(
                f"{payment.type_payment.capitalize()} payment recorded successfully",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        except Payment.DoesNotExist:
            response, code = custom_error_response(
                "NotFound",
                "Payment not found"
            )
            return Response(response, status=code)

        except stripe.error.StripeError as e:
            response, code = custom_error_response(
                "StripeError",
                str(e)
            )
            return Response(response, status=code)

        except Exception as e:
            response, code = custom_error_response(
                "ServerError",
                str(e)
            )
            return Response(response, status=code)



