from django.utils import timezone
import math
from infrastructure.models import Tarifa

class CloseTicket:

    def __init__(self, ticket_repo, spot_repo):
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo

    def execute(self, vehicle):
        ticket = self.ticket_repo.get_active_by_vehicle(vehicle.id)

        if not ticket:
            raise Exception(f"No hay ticket activo para la placa {vehicle.license_plate}")

        config = Tarifa.get_config()

        if vehicle.type == 'MOTORCYCLE':
            tarifa_minuto = config.tarifa_moto / 60
        else:
            tarifa_minuto = config.tarifa_carro / 60

        exit_time = timezone.now()
        duration = exit_time - ticket.entry_time
        minutos_a_cobrar = math.ceil(duration.total_seconds() / 60)

        if minutos_a_cobrar <= 0:
            minutos_a_cobrar = 1

        total = minutos_a_cobrar * tarifa_minuto

        if vehicle.client:
            nombre = vehicle.client.name.strip().lower()
            tipo = getattr(vehicle.client, 'client_type', 'REGULAR')

            if nombre != "visitante":
                if tipo == 'SENA':
                    total = total * (1 - config.descuento_sena / 100)
                elif tipo == 'TRABAJADOR':
                    total = total * (1 - config.descuento_trabajador / 100)
                else:
                    total = total * (1 - config.descuento_registrado / 100)

        ticket.exit_time = exit_time
        ticket.tarifa = config
        ticket.total_paid = int(total)
        ticket.status = "CLOSED"
        self.ticket_repo.save(ticket)

        if ticket.parking_spot_id:
            self.spot_repo.free(ticket.parking_spot_id)

        return ticket