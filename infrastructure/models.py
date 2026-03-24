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
    created_at = models.DateTimeField(auto_now_add=True)



class Client(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'client' 
    def __str__(self):
        return self.name


class Vehicle(models.Model):

    VEHICLE_TYPES = [
        ('CAR', 'Carro'),
        ('MOTORCYCLE', 'Moto'),
        ('BICYCLE', 'Bici'),
    ]

    license_plate = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicle' 

    def __str__(self):
        return self.license_plate
    
    
class Ticket(models.Model):
    vehicle = models.ForeignKey('Vehicle', on_delete=models.CASCADE)
    parking_spot = models.ForeignKey('ParkingSpot', on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True)

    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)

    total_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=20, default='ACTIVE')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket'

class ParkingSpot(models.Model):
    number = models.IntegerField(unique=True)
    type = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'parking_spot'



class Payment(models.Model):
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('TRANSFER', 'Transfer'),
    ]

    ticket = models.ForeignKey('Ticket', on_delete = models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete = models.SET_NULL, null = True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"payment {self.id} - {self.amount}"
