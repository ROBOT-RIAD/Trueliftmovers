from django.db import models
from truck.models import Truck
from accounts.models import User
from .constants import STATUS_CHOICES
from django.utils import timezone
from decimal import Decimal


# Create your models here.


class Booking(models.Model):
    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,related_name='bookings')
    truck =models.ForeignKey(Truck,on_delete=models.SET_NULL,null=True,blank=True,related_name='bookings')
    preference_track = models.JSONField(null=True,blank=True,help_text="Price snapshot at booking time")
    movers = models.JSONField(null=True,blank=True,help_text="Movers snapshot at booking time")


    # Pickup Info
    pickup_time = models.DateTimeField()
    pickup_address = models.TextField()
    pickup_lat = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_lng = models.DecimalField(max_digits=9, decimal_places=6)

    
    # Drop-off Info
    drop_off_address = models.TextField()
    drop_lat = models.DecimalField(max_digits=9, decimal_places=6)
    drop_lng = models.DecimalField(max_digits=9, decimal_places=6)


    # Booking Details
    movable_items = models.TextField(null=True, blank=True)
    initial_price = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    movers_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='pending')

    # Payment Status
    truck_payment_status = models.BooleanField(default=False)
    mover_payment_status = models.BooleanField(default=False)
    

    
    # Google Maps
    overview_polyline = models.TextField(help_text="Encoded polyline from Google Directions API",null=True,blank=True)
    distance_meter = models.PositiveIntegerField(help_text="Total distance in meters",null=True,blank=True)
    duration_second = models.PositiveIntegerField(help_text="Total duration in seconds",null=True,blank=True)


    admin_note = models.TextField(null=True, blank=True, help_text="Admin internal note")


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Start booking
        if self.status == 'start' and self.start_time is None:
            self.start_time = timezone.now()

        # End booking
        if self.status == 'end' and self.end_time is None:
            self.end_time = timezone.now()
            self.calculate_movers_total()

        super().save(*args, **kwargs)
    def calculate_movers_total(self):
        if not self.start_time or not self.end_time or not self.movers:
            return

        duration_seconds = (self.end_time - self.start_time).total_seconds()
        hours = Decimal(duration_seconds) / Decimal(3600)
        
        hourly_rate = Decimal(self.movers.get("hour_rate",0))

        self.movers_total = hours * hourly_rate

    def __str__(self):
        return f"Booking #{self.id}"




class BookingAgreement(models.Model):
    booking = models.OneToOneField(Booking,on_delete=models.CASCADE,related_name='agreement')
    agreements = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking Agreement {self.id}"


    




