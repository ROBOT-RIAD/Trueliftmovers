from django.db import models
from accounts.models import User

# Create your models here.


class Support(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='support')
    title = models.CharField(max_length=200)
    text = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Support Request: {self.title} by {self.user.username}"
    
    
