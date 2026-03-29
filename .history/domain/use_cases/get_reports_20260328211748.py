class GetReportsUseCase:
    """
    Caso de uso para manejar los reportes.
    Aquí vive toda la lógica de negocio.
    """

    def __init__(self, report_repository):
        self.report_repository = report_repository

    # ======================
    # INGRESOS
    # ======================
    def get_daily_income(self, date=None):
        """Ingresos de un día."""
        return self.report_repository.get_daily_income(date)

    def get_monthly_income(self, year=None, month=None):
        """Ingresos del mes, organizados por día."""
        return self.report_repository.get_monthly_income(year, month)

    # ======================
    # CLIENTES
    # ======================
    def get_frequent_clients(self, limit=10):
        """Clientes que más han venido."""
        return self.report_repository.get_frequent_clients(limit)

    # ======================
    # VEHÍCULOS
    # ======================
    def get_vehicle_type_stats(self):
        """Cantidad de servicios por tipo de vehículo."""
        return self.report_repository.get_vehicle_type_stats()

    # ======================
    # OPERACIÓN
    # ======================
    def get_usage_stats(self):
        """Resumen general: activos y total histórico."""
        return self.report_repository.get_usage_stats()