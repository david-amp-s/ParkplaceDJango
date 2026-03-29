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
from .models import ParkingSpot

from django.db.models import Sum, Count, Q
from django.db.models.functions import ExtractWeekDay, TruncDay
from django.utils import timezone
from .models import Ticket

class DjangoReportRepository:
    
    def get_financial_summary(self):
        hoy = timezone.now().date()
        inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
        inicio_mes = hoy.replace(day=1)

        metrics = Ticket.objects.filter(status="CLOSED").aggregate(
            hoy=Sum('total_paid', filter=Q(exit_time__date=hoy)),
            semana=Sum('total_paid', filter=Q(exit_time__date__gte=inicio_semana)),
            mes=Sum('total_paid', filter=Q(exit_time__date__gte=inicio_mes)),
            tickets_hoy=Count('id', filter=Q(exit_time__date=hoy))
        )

        return {
            "hoy": float(metrics['hoy'] or 0),
            "semana": float(metrics['semana'] or 0),
            "mes": float(metrics['mes'] or 0),
            "tickets_hoy": metrics['tickets_hoy'] or 0
        }

    def get_revenue_by_day_of_week(self):
        dias_nombres = {1: "Dom", 2: "Lun", 3: "Mar", 4: "Mié", 5: "Jue", 6: "Vie", 7: "Sáb"}
        stats = Ticket.objects.filter(
            status="CLOSED", 
            exit_time__gte=timezone.now() - timezone.timedelta(days=30)
        ).annotate(dia_num=ExtractWeekDay('exit_time')).values('dia_num').annotate(total=Sum('total_paid')).order_by('dia_num')
        
        return [{"nombre": dias_nombres.get(s['dia_num']), "total": float(s['total'] or 0)} for s in stats]

    def get_stay_metrics(self):
        tickets = Ticket.objects.filter(status="CLOSED", exit_time__isnull=False, entry_time__isnull=False)
        duraciones = [(t.exit_time - t.entry_time).total_seconds() / 60 for t in tickets]
        return {
            "avg_time": round(sum(duraciones) / len(duraciones), 1) if duraciones else 0,
            "max_time": round(max(duraciones), 1) if duraciones else 0
        }

    def get_vehicle_type_stats(self):
        return Ticket.objects.values('vehicle__type').annotate(total_services=Count('id')).order_by('-total_services')

    def get_frequent_clients(self):
        # Usamos los nombres de campos exactos de tu modelo
        return Ticket.objects.values('vehicle__client__name', 'vehicle__client__phone').annotate(visit_count=Count('id')).order_by('-visit_count')[:5]

    def get_monthly_income(self):
        return Ticket.objects.filter(status="CLOSED", exit_time__month=timezone.now().month).annotate(day=TruncDay('exit_time')).values('day').annotate(total=Sum('total_paid'), ticket_count=Count('id')).order_by('-day')