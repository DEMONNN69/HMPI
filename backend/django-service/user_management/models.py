# user_management/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    USER_ROLES = [
        ('admin', 'Administrator'),
        ('analyst', 'Data Analyst'),
        ('field_worker', 'Field Worker'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=USER_ROLES, default='viewer')
    organization = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
