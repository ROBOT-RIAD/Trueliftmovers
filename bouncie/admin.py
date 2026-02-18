from django.contrib import admin
from .models import BouncieToken


@admin.register(BouncieToken)
class BouncieTokenAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'token_type', 'expires_in', 'updated_at', 'is_expired')
    readonly_fields = ('created_at', 'updated_at')
