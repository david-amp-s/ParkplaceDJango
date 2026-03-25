# use_cases/close_ticket.py
from django.utils import timezone

class CloseTicket:

    def __init__(self, ticket_repo, spot_repo, rate_repo):
        """
        ticket_repo: repositorio para manejar Ticket
        spot_repo: repositorio para manejar ParkingSpot
        rate_repo: repositorio para manejar VehicleRate
        """
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo
        self.rate_repo = rate_repo

    def execute(self, vehicle):
        from infrastructure.models import Ticket

        # Obtener ticket activo del vehículo
        ticket = Ticket.objects.filter(vehicle_id=vehicle.id, status='ACTIVE').first()
        if not ticket:
            raise Exception("No hay ticket activo para este vehículo")

        exit_time = timezone.now()
        entry_time = ticket.entry_time
        duration = exit_time - entry_time
        seconds = duration.total_seconds()

        # Calcular horas a cobrar (mínimo 1)
        hours_to_charge = int(seconds // 3600) + (1 if seconds % 3600 > 0 else 0)
        hours_to_charge = max(hours_to_charge, 1)

        # Obtener tarifa según tipo de vehículo
        rate_obj = self.rate_repo.get_by_vehicle_type(vehicle.type)
        if not rate_obj:
            raise Exception(f"Tarifa no configurada para tipo {vehicle.type}")

        base_rate = float(rate_obj.price_per_hour)

        # Aplicar descuento si el cliente no es visitante
        if vehicle.client and vehicle.client.name != "Visitante":
            base_rate *= 0.8

        total = int(hours_to_charge * base_rate)

        # Actualizar ticket
        ticket.exit_time = exit_time
        ticket.total_paid = total
        ticket.status = "CLOSED"
        ticket.save()

        # Liberar espacio
        self.spot_repo.free(ticket.parking_spot_id)

        return total