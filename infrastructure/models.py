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

class Payment(models.Model):
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('TRANSFER', 'Transfer'),
    ]

    ticket = models.ForeignKey('Ticket', on_delete = models.CASCADE)
    employee = models.ForeignKey('Employe', on_delete = models.SET_NULL, null = True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"payment {self.id} - {self.amount}"