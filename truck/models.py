from django.db import models
from .constants import STATUS_CHOICES,TRUCK_TYPE_CHOICES
# Create your models here.


class Truck(models.Model):
    truck_number_plate = models.CharField(max_length=300, unique=True)
    truck_size = models.CharField(max_length=150,null=True, blank=True)
    truck_capacity = models.CharField(max_length=150,null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,null=True, blank=True)
    driver_name = models.CharField(max_length=150,null=True, blank=True)
    driver_phone_number = models.CharField(max_length=20,null=True, blank=True)
    license_number = models.CharField(max_length=100,null=True, blank=True)
    inspection_date = models.DateField(null=True, blank=True)
    insurance_details = models.FileField(upload_to='./media/insurance_docs/', null=True, blank=True)
    truck_type = models.CharField(max_length=50,choices=TRUCK_TYPE_CHOICES,default="box",null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.truck_number_plate} - {self.driver_name}"




class PriceManagement(models.Model):
    truck_size = models.CharField(max_length=150)
    minimum_distance = models.FloatField(help_text="Minimum distance (in KM) covered by minimum charge")
    minimum_charge = models.FloatField(help_text="Base charge for minimum distance")
    unite_price = models.FloatField(help_text="Charge per extra KM after minimum distance")

    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)



class MoversManagements(models.Model):
    movers_number = models.PositiveIntegerField()
    hour_rate = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Movers: {self.movers_number} | Rate: {self.hour_rate}/hr"
