from django.contrib import admin
from .models import Truck,PriceManagement,MoversManagements

# Register your models here.

@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ('id','truck_number_plate','truck_size','truck_capacity','status','driver_name','driver_phone_number','license_number','inspection_date','insurance_details','created_at','updated_at')
    search_fields = ('truck_number_plate','driver_name','driver_phone_number','license_number')
    list_filter = ('status', 'truck_size')





@admin.register(PriceManagement)
class PriceManagementAdmin(admin.ModelAdmin):
    list_display = ('id','truck_size','minimum_distance','minimum_charge','unite_price','create_at','update_at',)
    list_filter = ('truck_size','create_at',)
    search_fields = ('truck_size',)
    ordering = ('-create_at',)



@admin.register(MoversManagements)
class MoversManagementsAdmin(admin.ModelAdmin):
    list_display = ('id','movers_number','hour_rate','created_at','updated_at',)
    list_filter = ('created_at', 'updated_at')
    search_fields = ('movers_number',)
    ordering = ('-created_at',)

