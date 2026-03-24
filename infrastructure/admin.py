from django.contrib import admin
from .models import Vehicle, Client, Ticket, ParkingSpot, Payment

admin.site.register(Vehicle)
admin.site.register(Client)
admin.site.register(Ticket)
admin.site.register(ParkingSpot)
admin.site.register(Payment)