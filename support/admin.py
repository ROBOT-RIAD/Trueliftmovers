from django.contrib import admin
from .models import Support
# Register your models here.



@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'short_text','user', 'resolved', 'created_at', 'updated_at')
    list_filter = ('resolved', 'created_at', 'updated_at')
    search_fields = ('title', 'text', 'user__username', 'user__email')
    ordering = ('-created_at',)

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    short_text.short_description = "Text Preview"
