from django.utils import timezone
import math
from infrastructure.models import Tarifa

class CloseTicket:

    def __init__(self, ticket_repo, spot_repo):
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo

    def _calcular_total(self, ticket, vehicle, exit_time):
        config = Tarifa.get_config()

        tarifa_minuto = (
            config.tarifa_moto / 60
            if vehicle.type == 'MOTORCYCLE'
            else config.tarifa_carro / 60
        )

        duration = exit_time - ticket.entry_time
        minutos = max(math.ceil(duration.total_seconds() / 60), 1)
        total = minutos * tarifa_minuto

        if vehicle.client:
            nombre = vehicle.client.name.strip().lower()
            tipo = getattr(vehicle.client, 'client_type', 'REGULAR')

            if nombre != "visitante":
                if tipo == 'SENA':
                    total *= (1 - config.descuento_sena / 100)
                elif tipo == 'TRABAJADOR':
                    total *= (1 - config.descuento_trabajador / 100)
                else:
                    total *= (1 - config.descuento_registrado / 100)

        return int(total), minutos, config

    def preview(self, vehicle):
        ticket = self.ticket_repo.get_active_by_vehicle(vehicle.id)

        if not ticket:
            raise Exception(f"No hay ticket activo para la placa {vehicle.license_plate}")

        exit_time = timezone.now()
        duration = exit_time - ticket.entry_time
        total_segundos = int(duration.total_seconds())

        total, minutos, _ = self._calcular_total(ticket, vehicle, exit_time)

        return {
            "total": total,
            "minutos": minutos,
            "segundos_totales": total_segundos,
            "entry_time": ticket.entry_time,
        }

    def execute(self, vehicle):
        ticket = self.ticket_repo.get_active_by_vehicle(vehicle.id)

        if not ticket:
            raise Exception(f"No hay ticket activo para la placa {vehicle.license_plate}")

        exit_time = timezone.now()
        total, _, config = self._calcular_total(ticket, vehicle, exit_time)

        ticket.exit_time = exit_time
        ticket.tarifa = config
        ticket.total_paid = total
        ticket.status = "CLOSED"
        self.ticket_repo.save(ticket)

        if ticket.parking_spot_id:
            self.spot_repo.free(ticket.parking_spot_id)

        return ticket