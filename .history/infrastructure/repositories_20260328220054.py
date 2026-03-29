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

# --- REPORT REPOSITORY (AJUSTADO A TUS MODELOS) ---
class DjangoReportRepository(ReportRepositoryPort):
    TICKET_TABLE = 'ticket' # Usaremos esta para el dinero también
    
    def get_financial_summary(self):
        """Cambiado para leer de TICKET igual que el dashboard"""
        sql = f"""
            SELECT 
                COALESCE(SUM(total_paid), 0) FILTER (WHERE exit_time::date = CURRENT_DATE) as hoy,
                COALESCE(SUM(total_paid), 0) FILTER (WHERE exit_time >= DATE_TRUNC('week', CURRENT_DATE)) as semana,
                COALESCE(SUM(total_paid), 0) FILTER (WHERE exit_time >= DATE_TRUNC('month', CURRENT_DATE)) as mes,
                COUNT(id) FILTER (WHERE exit_time::date = CURRENT_DATE AND status = 'CLOSED') as tickets_hoy
            FROM {self.TICKET_TABLE}
            WHERE status = 'CLOSED'
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            return {
                "hoy": float(row[0] or 0),
                "semana": float(row[1] or 0),
                "mes": float(row[2] or 0),
                "tickets_hoy": row[3] or 0
            }

    def get_revenue_by_day_of_week(self):
        """Cambiado a TICKET"""
        sql = f"""
            SELECT 
                TO_CHAR(exit_time, 'ID') as dia_num,
                TO_CHAR(exit_time, 'TMDay') as dia_nombre,
                SUM(total_paid) as total
            FROM {self.TICKET_TABLE}
            WHERE exit_time >= CURRENT_DATE - INTERVAL '30 days'
              AND status = 'CLOSED'
            GROUP BY dia_num, dia_nombre
            ORDER BY dia_num
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [{"nombre": r[1].strip(), "total": float(r[2] or 0)} for r in rows]