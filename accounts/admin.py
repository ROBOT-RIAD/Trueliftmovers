from django.contrib import admin
from .models import User,Profile,PasswordReserOTP

# Register your models here.

#admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id","email" ,"role"]
    search_fields =["email","role"]
    list_filter =["role"]



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display=["id","user","full_name","phone","country","created_at","updated_at"]
    search_fields = ["full_name", "phone", "user__email"]
    list_filter = ["country"]


@admin.register(PasswordReserOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'created_at', 'is_verified')
    search_fields = ('user__email', 'otp')
    list_filter = ('is_verified',)
    ordering = ('created_at',)




