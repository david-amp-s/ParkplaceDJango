from django.db import models



class EmployeeModel(models.Model):
    
    ROLE_CHOICES = [
        ('ADMIN', 'ADMIN'),
        ('EMPLOYEE', 'EMPLOYEE')
    ]


    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, null=True, blank=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "employee"


class Client(models.Model):
    CLIENT_TYPES = [
        ('REGULAR', 'Cliente Regular'),
        ('SENA', 'Aprendiz SENA'),
        ('TRABAJADOR', 'Trabajador'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=100, null=True, blank=True)
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES, default='REGULAR')
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


class ParkingSpot(models.Model):
    number = models.IntegerField(unique=True)
    type = models.CharField(max_length=20)
    status = models.CharField(max_length=20, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'parking_spot'

    def occupy(self):
        self.status = 'OCCUPIED'
        self.save()

    def release(self):
        self.status = 'AVAILABLE'
        self.save()


class Ticket(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    parking_spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeeModel, on_delete=models.SET_NULL, null=True)

    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField(null=True, blank=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket'
        ordering = ['-entry_time'] 


class Payment(models.Model):
    METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('TRANSFER', 'Transfer'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeeModel, on_delete=models.SET_NULL, null=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"payment {self.id} - {self.amount}"
    
    class Meta:
        db_table = 'payment'

class Tarifa(models.Model):
    tarifa_carro = models.IntegerField(default=3000)
    tarifa_moto = models.IntegerField(default=2000)
    descuento_registrado = models.IntegerField(default=20)  # porcentaje ej: 20 = 20%
    updated_at = models.DateTimeField(auto_now=True)
    descuento_sena        = models.IntegerField(default=50)
    descuento_trabajador  = models.IntegerField(default=30)

    class Meta:
        db_table = 'tarifa'

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(id=1, defaults={
            'tarifa_carro': 3000,
            'tarifa_moto': 2000,
            'descuento_registrado': 20
        })
        return obj