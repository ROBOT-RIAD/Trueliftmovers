from django.contrib import admin
from .models import Payment



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id','booking','type_payment','amount','currency','stripe_payment_method_id', 'status','is_paid','stripe_payment_intent_id','paid_at','created_at')
    list_filter = ('type_payment','status','is_paid','currency','created_at')
    search_fields = ('id','booking__id','stripe_payment_intent_id','stripe_payment_method_id')
    readonly_fields = ('stripe_payment_intent_id','stripe_payment_method_id','paid_at','created_at','updated_at')
    ordering = ('-created_at',)
    fieldsets = (
        ("Booking Information", {
            'fields': ('booking', 'type_payment')
        }),
        ("Payment Details", {
            'fields': (
                'amount',
                'currency',
                'status',
                'is_paid',
                'paid_at'
            )
        }),
        ("Stripe Info", {
            'fields': (
                'stripe_payment_intent_id',
                'stripe_payment_method_id'
            )
        }),
        ("Timestamps", {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )
