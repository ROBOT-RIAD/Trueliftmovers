from rest_framework import serializers
from booking.models import Booking
from .models import Payment

class CheckoutSessionSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    type_payment = serializers.ChoiceField(choices=['truck', 'mover'])



class PaymentSuccessSerializer(serializers.Serializer):
    session_id = serializers.CharField()




class BookingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"


class PaymentDetailSerializer(serializers.ModelSerializer):
    booking = BookingInfoSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ["id","type_payment","amount","currency","status","is_paid","paid_at","stripe_payment_intent_id","stripe_payment_method_id","created_at","booking",]
