from django.contrib import admin
from .models import BouncieToken, VehicleEvent


@admin.register(BouncieToken)
class BouncieTokenAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'token_type', 'expires_in', 'updated_at', 'is_expired')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(VehicleEvent)
class VehicleEventAdmin(admin.ModelAdmin):
    list_display = ('imei', 'event_type', 'transaction_id', 'lat', 'lon', 'speed', 'received_at')
    list_filter = ('event_type', 'imei')
    search_fields = ('imei', 'transaction_id')
    readonly_fields = ('received_at',)
