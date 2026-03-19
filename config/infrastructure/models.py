from django.db import models

class AppUser(models.Model):
    ROLE_CHOICES =[
        ('ADMIN','ADMIN'),
        ('EMPLOYEE', 'EMPLOYEE')
    ]
    
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
class Employee(models.Model):
    user = models.OneToOneField(AppUser, on_delete = models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, null=True , blank=True)
    create_at = models.DateTimeField(auto_now_add=True)