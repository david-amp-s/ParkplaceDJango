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

        # Tarifa según tipo de vehículo
        if vehicle.type == 'MOTORCYCLE':
            tarifa = config.tarifa_moto
        else:
            tarifa = config.tarifa_carro  # CAR y cualquier otro

        exit_time = timezone.now()
        duration = exit_time - ticket.entry_time
        horas_a_cobrar = math.ceil(duration.total_seconds() / 3600)

        if horas_a_cobrar <= 0:
            horas_a_cobrar = 1

        total = horas_a_cobrar * tarifa

        # Descuento si es cliente registrado (no visitante)
        es_registrado = (
            vehicle.client and
            vehicle.client.name.strip().lower() != "visitante"
        )
        if es_registrado:
            total = total * (1 - config.descuento_registrado / 100)

        ticket.exit_time = exit_time
        ticket.total_paid = int(total)
        ticket.status = "CLOSED"
        self.ticket_repo.save(ticket)

        if ticket.parking_spot_id:
            self.spot_repo.free(ticket.parking_spot_id)

        return ticket.total_paid