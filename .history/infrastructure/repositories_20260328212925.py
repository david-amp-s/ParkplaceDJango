from datetime import date as dt_date, datetime
from django.db import connection
from django.shortcuts import render

# =========================
# EMPLOYEE REPOSITORY
# =========================
from domain.entities.employee import Employee as EmployeeEntity
from domain.ports.employee_repository import EmployeeRepository
from .models import EmployeeModel

class DjangoEmployeeRepository(EmployeeRepository):

    def find_by_username(self, username):
        try:
            e = EmployeeModel.objects.get(username=username)
            return EmployeeEntity(
                id=e.id,
                name=e.name,
                phone=e.phone,
                username=e.username,
                password=e.password,
                role=e.role,
                created_at=e.created_at
            )
        except EmployeeModel.DoesNotExist:
            return None

    def create(self, data):
        return EmployeeModel.objects.create(**data)

    def get_all(self):
        return [
            EmployeeEntity(
                e.id, e.name, e.phone, e.username, e.password, e.role, e.created_at
            )
            for e in EmployeeModel.objects.all()
        ]

    def get_by_id(self, employee_id):
        try:
            e = EmployeeModel.objects.get(id=employee_id)
            return EmployeeEntity(
                e.id, e.name, e.phone, e.username, e.password, e.role, e.created_at
            )
        except EmployeeModel.DoesNotExist:
            return None

    def delete(self, employee_id):
        EmployeeModel.objects.filter(id=employee_id).delete()


# =========================
# REPORT REPOSITORY (ARREGLADO)
# =========================

from domain.ports.report_repository import ReportRepositoryPort

class DjangoReportRepository(ReportRepositoryPort):

    # 🔥 AJUSTA ESTO SEGÚN TU MODELO REAL
    PAYMENT_TABLE = "payment"
    PAYMENT_DATE_FIELD = "payment_date"  # CAMBIA a created_at si usas ese

    def get_daily_income(self, target_date=None):
        target_date = target_date or dt_date.today()

        sql = f"""
            SELECT
                COUNT(*) AS ticket_count,
                COALESCE(SUM(amount), 0) AS total
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
                COALESCE(SUM(amount), 0) AS total
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
            {"day": str(r[0]), "ticket_count": r[1], "total": float(r[2])}
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
        """

        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

        return [
            {"vehicle_type": r[0], "total_services": r[1]}
            for r in rows
        ]

    def get_frequent_clients(self, limit=10):
        sql = """
            SELECT
                c.name,
                COUNT(t.id) as visits
            FROM ticket t
            JOIN vehicle v ON v.id = t.vehicle_id
            JOIN client c ON c.id = v.client_id
            GROUP BY c.name
            ORDER BY visits DESC
            LIMIT %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [limit])
            rows = cursor.fetchall()

        return [
            {"name": r[0], "visit_count": r[1]}
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


# =========================
# DASHBOARD VIEW (CORREGIDO)
# =========================

def reports_dashboard(request):
    uc = _get_report_use_case()

    selected_year  = int(request.GET.get("year", datetime.today().year))
    selected_month = int(request.GET.get("month", datetime.today().month))
    selected_date  = request.GET.get("date")

    try:
        daily_date = datetime.strptime(selected_date, "%Y-%m-%d").date() if selected_date else dt_date.today()
    except:
        daily_date = dt_date.today()

    # REPORTES
    daily_income = uc.get_daily_income(daily_date)
    monthly_income = uc.get_monthly_income(selected_year, selected_month)
    vehicle_stats = uc.get_vehicle_type_stats()
    frequent_clients = uc.get_frequent_clients(limit=10)
    usage_stats = uc.get_usage_stats()

    total_tickets = usage_stats.get("total_tickets", 0)
    total_income = daily_income.get("total", 0)

    average_ticket = total_income / total_tickets if total_tickets else 0

    context = {
        "selected_year": selected_year,
        "selected_month": selected_month,
        "selected_date": str(daily_date),

        "daily_income": daily_income,
        "monthly_income": monthly_income,
        "income_by_vehicle_type": vehicle_stats,
        "client_type_stats": frequent_clients,
        "usage_stats": usage_stats,

        "average_ticket": round(average_ticket, 2),
        "occupancy_rate": usage_stats.get("active", 0),
    }

    return render(request, "reports.html", context)