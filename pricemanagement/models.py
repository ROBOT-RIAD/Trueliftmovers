from django.db import models

# Create your models here.

class PriceManagement(models.Model):
    minimum_distance = models.PositiveIntegerField()
    minimum_charge = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

