from django.db import models
from booking.models import Booking
from .constants import PAYMENT_TYPE_CHOICES,PAYMENT_STATUS_CHOICES

# Create your models here.



class Payment(models.Model):
    booking = models.ForeignKey(Booking,on_delete=models.CASCADE,related_name='payments')
    type_payment = models.CharField(max_length=20,choices=PAYMENT_TYPE_CHOICES)
    stripe_payment_intent_id = models.CharField(max_length=255,null=True,blank=True)
    stripe_payment_method_id = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    currency = models.CharField(max_length=10,default='usd')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.id} - Booking #{self.booking.id}"
