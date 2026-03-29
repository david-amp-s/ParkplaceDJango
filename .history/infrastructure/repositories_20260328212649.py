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


class DjangoReportRepository(ReportRepositoryPort):
    """
    Implementación concreta del repositorio de reportes.
    Usa raw SQL sobre la BD PostgreSQL definida en BASE_DE_DATOS.txt.

    Tablas utilizadas según especificación:
      - Ingresos            → ticket
      - Estadísticas de uso → ticket
      - Vehículos frecuentes → ticket + vehicle
      - Clientes frecuentes  → ticket + vehicle + client
    """

    # ------------------------------------------------------------------
    # 1. INGRESOS DIARIOS
    # ------------------------------------------------------------------
    def get_daily_income(self, date=None):
        """
        Retorna el total recaudado en pagos para una fecha dada.
        Si no se pasa fecha, usa hoy.
        Returns: dict con 'date', 'total', 'ticket_count'
        """
        target = date or datetime.today().date()

        sql = """
            SELECT
                DATE(payment_date)          AS day,
                COUNT(*)                    AS ticket_count,
                COALESCE(SUM(amount), 0)    AS total
            FROM payment
            WHERE DATE(payment_date) = %s
            GROUP BY DATE(payment_date)
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [target])
            row = cursor.fetchone()

        if row:
            return {"date": row[0], "ticket_count": row[1], "total": float(row[2])}
        return {"date": target, "ticket_count": 0, "total": 0.0}

    # ------------------------------------------------------------------
    # 2. INGRESOS MENSUALES (agrupados por día)
    # ------------------------------------------------------------------
    def get_monthly_income(self, year=None, month=None):
        """
        Retorna lista de ingresos agrupados por día para el mes indicado.
        Si no se pasan parámetros, usa el mes actual.
        Returns: list of dicts {day, total, ticket_count}
        """
        today = datetime.today()
        y = year or today.year
        m = month or today.month

        sql = """
            SELECT
                DATE(payment_date)          AS day,
                COUNT(*)                    AS ticket_count,
                COALESCE(SUM(amount), 0)    AS total
            FROM payment
            WHERE EXTRACT(YEAR  FROM payment_date) = %s
              AND EXTRACT(MONTH FROM payment_date) = %s
            GROUP BY DATE(payment_date)
            ORDER BY day
        """
        with connection.cursor() as cursor:
            cursor.execute(sql, [y, m])
            rows = cursor.fetchall()

        return [
            {"day": str(r[0]), "ticket_count": r[1], "total": float(r[2])}
            for r in rows
        ]

    # ------------------------------------------------------------------
    # 3. TIPO DE VEHÍCULOS (estadísticas de uso)
    # ------------------------------------------------------------------
    def get_vehicle_type_stats(self):
        """
        Retorna cuántos tickets se han emitido por tipo de vehículo.
        Tablas: ticket JOIN vehicle
        Returns: list of dicts {vehicle_type, total_services, active_now}
        """
        sql = """
            SELECT
                v.type                              AS vehicle_type,
                COUNT(t.id)                         AS total_services,
                COUNT(t.id) FILTER (WHERE t.status = 'ACTIVE') AS active_now
            FROM ticket t
            JOIN vehicle v ON v.id = t.vehicle_id
            GROUP BY v.type
            ORDER BY total_services DESC
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        return [
            {
                "vehicle_type": r[0],
                "total_services": r[1],
                "active_now": r[2],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # 4. CLIENTES FRECUENTES
    # ------------------------------------------------------------------
    def get_frequent_clients(self, limit=10):
        """
        Retorna los clientes con más visitas (tickets cerrados o activos).
        Tablas: ticket JOIN vehicle JOIN client
        Returns: list of dicts ordenados por visit_count desc
        """
        sql = """
            SELECT
                c.id,
                c.name,
                c.phone,
                c.email,
                COUNT(t.id)  AS visit_count,
                MAX(t.entry_time) AS last_visit
            FROM ticket t
            JOIN vehicle v ON v.id = t.vehicle_id
            JOIN client  c ON c.id = v.client_id
            GROUP BY c.id, c.name, c.phone, c.email
            ORDER BY visit_count DESC
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
                "email": r[3],
                "visit_count": r[4],
                "last_visit": r[5],
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # 5. ESTADÍSTICAS GENERALES DE USO
    # ------------------------------------------------------------------
    def get_usage_stats(self):
        """
        Retorna métricas globales del parqueadero.
        Tablas: ticket
        Returns: dict con totales
        """
        sql = """
            SELECT
                COUNT(*)                                        AS total_services,
                COUNT(*) FILTER (WHERE status = 'ACTIVE')      AS active_vehicles,
                COUNT(*) FILTER (WHERE status = 'CLOSED')      AS completed_services,
                COALESCE(SUM(total_paid), 0)                    AS total_revenue
            FROM ticket
        """
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()

        return {
            "total_services": row[0],
            "active_vehicles": row[1],
            "completed_services": row[2],
            "total_revenue": float(row[3]),
        }