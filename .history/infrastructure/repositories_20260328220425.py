from django.db import connection
from django.utils import timezone
from datetime import date, datetime

# Entidades de Dominio
from domain.entities.employee import Employee as EmployeeEntity
from domain.entities.client import Client as ClientEntity
from domain.ports.employee_repository import EmployeeRepository
from domain.ports.report_repository import ReportRepositoryPort

# Modelos de Infraestructura
from .models import (
    Client as ClientModel, 
    EmployeeModel, 
    ParkingSpot, 
    Payment as PaymentModel,
    Ticket, 
    Vehicle as VehicleModel
)

# --- EMPLOYEE REPOSITORY ---
class DjangoEmployeeRepository(EmployeeRepository):
    def find_by_username(self, username):
        try:
            employee = EmployeeModel.objects.get(username=username)
            return EmployeeEntity(
                id=employee.id,
                name=employee.name,
                phone=employee.phone,
                username=employee.username,
                password=employee.password,
                role=employee.role,
                created_at=employee.created_at
            )
        except EmployeeModel.DoesNotExist:
            return None

    def create(self, data):
        return EmployeeModel.objects.create(**data)

    def get_all(self):
        return [
            EmployeeEntity(e.id, e.name, e.phone, e.username, e.password, e.role, e.created_at)
            for e in EmployeeModel.objects.all()
        ]

    def get_by_id(self, employee_id):
        try:
            e = EmployeeModel.objects.get(id=employee_id)
            return EmployeeEntity(e.id, e.name, e.phone, e.username, e.password, e.role, e.created_at)
        except EmployeeModel.DoesNotExist:
            return None

    def delete(self, employee_id):
        EmployeeModel.objects.filter(id=employee_id).delete()

# --- CLIENT REPOSITORY ---
class DjangoClientRepository:
    def save(self, client):
        return ClientModel.objects.create(
            name=client.name,
            phone=client.phone,
            email=client.email
        )

    def get_all(self):
        return ClientModel.objects.all()

# --- VEHICLE REPOSITORY ---
class DjangoVehicleRepository:
    def save(self, plate, v_type, client_id):
        return VehicleModel.objects.create(
            license_plate=plate, 
            type=v_type,         
            client_id=client_id 
        )

# --- TICKET REPOSITORY ---
class DjangoTicketRepository:
    def get_history_all(self):
        hoy = date.today() 
        return Ticket.objects.filter(
            entry_time__date=hoy 
        ).select_related('vehicle', 'vehicle__client').order_by('status', '-entry_time')

    def filter_by_plate(self, plate):
        hoy = date.today()
        return Ticket.objects.filter(
            vehicle__license_plate__icontains=plate,
            entry_time__date=hoy
        ).select_related('vehicle', 'vehicle__client').order_by('status', '-entry_time')

    def create(self, data):
        # Evitamos error si viene employee_id que no es campo directo en create
        data.pop('employee_id', None)
        return Ticket.objects.create(**data)

    def get_active_by_vehicle(self, vehicle_id):
        return Ticket.objects.filter(
            vehicle_id=vehicle_id,
            status='ACTIVE'
        ).first()

    def save(self, ticket):
        ticket.save()
        return ticket

# --- PARKING SPOT REPOSITORY ---
class DjangoParkingSpotRepository:
    def get_all(self):
        return ParkingSpot.objects.all().order_by('number')

    def get_available(self):
        return ParkingSpot.objects.filter(status='AVAILABLE').order_by('number').first()

    def get_by_id(self, spot_id):
        try:
            return ParkingSpot.objects.get(id=spot_id)
        except ParkingSpot.DoesNotExist:
            return None

    def occupy(self, spot_id):
        spot = self.get_by_id(spot_id)
        if spot:
            spot.status = 'OCCUPIED'
            spot.save()
        return spot

    def free(self, spot_id):
        spot = self.get_by_id(spot_id)
        if spot:
            spot.status = 'AVAILABLE'
            spot.save()
        return spot

# --- PAYMENT REPOSITORY ---
class DjangoPaymentRepository:
    def save(self, payment):
        return PaymentModel.objects.create(
            ticket_id=payment.ticket_id,
            employee_id=payment.employee_id,
            method=payment.method,
            amount=payment.amount
        )

from django.shortcuts import render
from datetime import date
from .repositories import DjangoReportRepository
from .models import ParkingSpot

def reports_view(request):
    repo = DjangoReportRepository()
    
    # Ejecutamos los métodos de tu repositorio
    finanzas = repo.get_financial_summary()
    comparativo_dias = repo.get_revenue_by_day_of_week()
    stay_metrics = repo.get_stay_metrics()
    vehicle_stats = repo.get_vehicle_type_stats()
    frequent_clients = repo.get_frequent_clients()
    monthly_income = repo.get_monthly_income()

    # Ocupación actual (Cálculo rápido para el Dashboard)
    total_spots = ParkingSpot.objects.count()
    occupied_count = ParkingSpot.objects.filter(status="OCCUPIED").count()
    ocupacion = int((occupied_count / total_spots) * 100) if total_spots > 0 else 0

    context = {
        "finanzas": finanzas,
        "comparativo_dias": comparativo_dias,
        "stay_avg": stay_metrics['avg_time'],
        "stay_max": stay_metrics['max_time'],
        "vehicle_stats": vehicle_stats,
        "frequent_clients": frequent_clients,
        "monthly_income": monthly_income,
        "occupancy_rate": ocupacion,
        "hoy": date.today(),
    }
    
    # ¡OJO! Asegúrate de que el nombre del archivo sea exactamente "reports.html"
    return render(request, "reports.html", context)