from django.db import connection
from datetime import datetime

from abc import ABC, abstractmethod


class ReportRepositoryPort(ABC):

    @abstractmethod
    def get_daily_income(self, date=None):
        pass

    @abstractmethod
    def get_monthly_income(self, year=None, month=None):
        pass

    @abstractmethod
    def get_vehicle_type_stats(self):
        pass

    @abstractmethod
    def get_frequent_clients(self, limit=10):
        pass

    @abstractmethod
    def get_usage_stats(self):
        pass

    def get_daily_income(self, date=None):
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

    def get_monthly_income(self, year=None, month=None):
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

    def get_vehicle_type_stats(self):
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

    def get_frequent_clients(self, limit=10):
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

    def get_usage_stats(self):
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