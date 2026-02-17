from django.contrib import admin
from .models import Booking,BookingAgreement

# Register your models here.

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id','user','truck','pickup_address','drop_off_address','initial_price','final_price','status','truck_payment_status',"start_time","end_time",'mover_payment_status','admin_note','created_at',)

    list_filter = ('status','truck_payment_status','mover_payment_status','created_at',)

    search_fields = ('id','user__email','pickup_address','drop_off_address',)

    readonly_fields = ('created_at','updated_at','overview_polyline','distance_meter','duration_second',)

    ordering = ('-created_at',)

    fieldsets = (
        ('User & Truck Info', {
            'fields': ('user', 'truck', 'status')
        }),
        ('Pickup Information', {
            'fields': ('pickup_time', 'pickup_address', 'pickup_lat', 'pickup_lng')
        }),
        ('Drop-off Information', {
            'fields': ('drop_off_address', 'drop_lat', 'drop_lng')
        }),
        ('Pricing', {
            'fields': ('initial_price', 'final_price')
        }),
        ('Payment Status', {
            'fields': ('truck_payment_status', 'mover_payment_status')
        }),
        ('Route Information (Google Maps)', {
            'fields': ('overview_polyline', 'distance_meter', 'duration_second')
        }),
        ('Extra Data', {
            'fields': ('preference_track', 'movers', 'movable_items')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(BookingAgreement)
class BookingAgreementAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'created_at', 'updated_at')
    search_fields = ('booking__id',)