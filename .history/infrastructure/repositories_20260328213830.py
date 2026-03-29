from datetime import date
from django.shortcuts import render
from django.utils import timezone

#Entidades de Dominio
from domain.entities.employee import Employee as EmployeeEntity
from domain.entities.client import Client as ClientEntity

from domain.ports.employee_repository import EmployeeRepository

#Modelos de Infraestructura
from .models import (Client as ClientModel, EmployeeModel, ParkingSpot, Payment as PaymentModel,
    Ticket, Vehicle as VehicleModel)




#EMPLOYEE REPOSITORY

class DjangoEmployeeRepository(EmployeeRepository):
    def find_by_username(self, username):
        return EmployeeModel.objects.filter(username=username).first()

    def create(self, data):
        return EmployeeModel.objects.create(**data)

    def get_all(self):
        return [
        EmployeeEntity(e.id, e.name, e.phone, e.username, e.password, e.role, e.created_at)
        for e in EmployeeModel.objects.all()
    ]

    def get_by_id(self, employee_id):
        e = EmployeeModel.objects.select_related('user').get(id=employee_id)
        return EmployeeModel(e.id, e.name, e.phone)

   

    def delete(self, employee_id):
        EmployeeModel.objects.get(id=employee_id).delete()
    
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

#CLIENT REPOSITORY

class DjangoClientRepository:
    def save(self, client):
        return ClientModel.objects.create(
            name=client.name,
            phone=client.phone,
            email=client.email
        )

    def get_all(self):
        return ClientModel.objects.all()

#VEHICLE REPOSITORY

class DjangoVehicleRepository:
    def save(self, plate, v_type, client_id):
        return VehicleModel.objects.create(
            license_plate=plate, 
            type=v_type,         
            client_id=client_id 
        )

#TICKET REPOSITORY

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

#PARKING SPOT REPOSITORY

from .models import ParkingSpot

class DjangoParkingSpotRepository:
    def get_all(self):
        """
        Trae TODOS los espacios de la base de datos 
        ordenados por 'number' (1, 2, 3...) para la cuadrícula.
        """
        return ParkingSpot.objects.all().order_by('number')

    def get_available(self):
        """Trae el primer espacio disponible que encuentre."""
        return ParkingSpot.objects.filter(status='AVAILABLE').order_by('number').first()

    def get_by_id(self, spot_id):
        """Busca un espacio específico por su ID primario."""
        try:
            return ParkingSpot.objects.get(id=spot_id)
        except ParkingSpot.DoesNotExist:
            return None

    def get_by_number(self, number):
        """Busca un espacio específico por su número visual."""
        try:
            return ParkingSpot.objects.get(number=number)
        except ParkingSpot.DoesNotExist:
            return None

    def occupy(self, spot_id):
        """Cambia el estado de un espacio a OCUPADO."""
        spot = self.get_by_id(spot_id)
        if spot:
            spot.status = 'OCCUPIED'
            spot.save()
        return spot

    def free(self, spot_id):
        """Cambia el estado de un espacio a DISPONIBLE."""
        spot = self.get_by_id(spot_id)
        if spot:
            spot.status = 'AVAILABLE'
            spot.save()
        return spot

    def update(self, spot_entity):
        """Actualiza un objeto de espacio completo usando los datos de la entidad."""
        spot = ParkingSpot.objects.get(id=spot_entity.id)
        spot.status = spot_entity.status
        spot.save()
        return spot

#PAYMENT REPOSITORY

class DjangoPaymentRepository:
    def save(self, payment):
        return PaymentModel.objects.create(
            ticket_id=payment.ticket_id,
            employee_id=payment.employee_id,
            method=payment.method,
            amount=payment.amount
        )
    
from django.db import connection
from datetime import date, datetime

from domain.ports.report_repository import ReportRepositoryPort


from django.db import connection
from datetime import date, datetime
from domain.ports.report_repository import ReportRepositoryPort


class DjangoReportRepository(ReportRepositoryPort):

    PAYMENT_TABLE = "infrastructure_payment"
    PAYMENT_DATE_FIELD = "created_at"
    PAYMENT_AMOUNT_FIELD = "amount"

    def get_daily_income(self, target_date=None):
        target_date = target_date or date.today()

        sql = f"""
            SELECT
                COUNT(*) AS ticket_count,
                COALESCE(SUM({self.PAYMENT_AMOUNT_FIELD}), 0) AS total
            FROM {self.PAYMENT_TABLE}
            WHERE DATE({self.PAYMENT_DATE_FIELD}) = %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [target_date])
            row = cursor.fetchone()

        return {
            "date": target_date,
            "ticket_count": row[0] if row else 0,
            "total": float(row[1]) if row else 0.0,
        }

    def get_monthly_income(self, year=None, month=None):
        today = datetime.today()
        y = year or today.year
        m = month or today.month

        sql = f"""
            SELECT
                DATE({self.PAYMENT_DATE_FIELD}) AS day,
                COUNT(*) AS ticket_count,
                COALESCE(SUM({self.PAYMENT_AMOUNT_FIELD}), 0) AS total
            FROM {self.PAYMENT_TABLE}
            WHERE EXTRACT(YEAR FROM {self.PAYMENT_DATE_FIELD}) = %s
              AND EXTRACT(MONTH FROM {self.PAYMENT_DATE_FIELD}) = %s
            GROUP BY DATE({self.PAYMENT_DATE_FIELD})
            ORDER BY day
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [y, m])
            rows = cursor.fetchall()

        return [
            {
                "day": str(r[0]),
                "ticket_count": r[1],
                "total": float(r[2]),
            }
            for r in rows
        ]

    def get_vehicle_type_stats(self):
        sql = """
            SELECT
                v.type,
                COUNT(t.id)
            FROM ticket t
            JOIN vehicle v ON v.id = t.vehicle_id
            GROUP BY v.type
            ORDER BY COUNT(t.id) DESC
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        return [
            {
                "vehicle_type": r[0],
                "total_services": r[1],
            }
            for r in rows
        ]

    def get_frequent_clients(self, limit=10):
        sql = """
            SELECT
                c.id,
                c.name,
                c.phone,
                COUNT(t.id) AS visits
            FROM ticket t
            JOIN vehicle v ON v.id = t.vehicle_id
            JOIN client c ON c.id = v.client_id
            GROUP BY c.id, c.name, c.phone
            ORDER BY visits DESC
            LIMIT %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [limit])
            rows = cursor.fetchall()

        return [
            {
                "client_id": r[0],
                "name": r[1],
                "phone": r[2],
                "visit_count": r[3],
            }
            for r in rows
        ]

    def get_usage_stats(self):
        sql = """
            SELECT
                COUNT(*) AS total_tickets,
                COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active,
                COUNT(*) FILTER (WHERE status = 'CLOSED') AS closed
            FROM ticket
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()

        return {
            "total_tickets": row[0] if row else 0,
            "active": row[1] if row else 0,
            "closed": row[2] if row else 0,
        }