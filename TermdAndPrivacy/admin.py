from django.contrib import admin
from .models import Terms, Privacy

# Register your models here.

@admin.register(Terms)
class TermsAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "created_at", "updated_at")
    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Text Preview"

@admin.register(Privacy)
class PrivacyAdmin(admin.ModelAdmin):
    list_display = ("id", "short_text", "created_at", "updated_at")
    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Text Preview"