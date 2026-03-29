class GetReportsUseCase:
    """
    Caso de uso para generar los 4 reportes del módulo de administración.
    Recibe un repositorio de reportes (puerto) por inyección de dependencias.
    """

    def __init__(self, report_repository):
        self.report_repository = report_repository

    def get_daily_income(self, date=None):
        """Ingresos del día actual o de una fecha específica."""
        return self.report_repository.get_daily_income(date)

    def get_monthly_income(self, year=None, month=None):
        """Ingresos agrupados por día dentro de un mes."""
        return self.report_repository.get_monthly_income(year, month)

    def get_vehicle_type_stats(self):
        """Cantidad de servicios (tickets) por tipo de vehículo."""
        return self.report_repository.get_vehicle_type_stats()

    def get_frequent_clients(self, limit=10):
        """Clientes con más tickets (visitas) registrados."""
        return self.report_repository.get_frequent_clients(limit)

    def get_usage_stats(self):
        """Vehículos activos ahora mismo y total de servicios históricos."""
        return self.report_repository.get_usage_stats()