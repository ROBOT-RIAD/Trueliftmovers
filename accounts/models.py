from django.db import models
from django.contrib.auth.models import AbstractUser
from .constants import ROLE_CHOICES
import random
from datetime import timedelta
from django.utils import timezone


# Create your models here.


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50,choices=ROLE_CHOICES,default="user")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']




class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="profile")
    full_name = models.CharField(max_length=200,blank=True,null=True)
    phone = models.CharField(max_length=20,blank=True,null=True)
    address = models.TextField(blank=True,null=True)
    country = models.CharField(max_length=100,blank=True,null=True)
    image = models.ImageField(upload_to='Media/Profile/',blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class PasswordReserOTP(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def save(self,*args, **kwargs):
        if not self.otp:
            self.otp = str(random.randint(1000,9999))
        super().save(*args, **kwargs)

    
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
         

