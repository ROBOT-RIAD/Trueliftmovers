from django.contrib import admin
from .models import Truck

# Register your models here.

@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('id','truck_number_plate','truck_size','truck_capacity','status','driver_name','driver_phone_number','license_number','inspection_date','insurance_details','created_at','updated_at')
    search_fields = ('truck_number_plate','driver_name','driver_phone_number','license_number')
    list_filter = ('status', 'truck_size')
