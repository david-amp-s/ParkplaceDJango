from django.utils import timezone
import math

class CloseTicket:
    TARIFA_UNICA = 3000

    def __init__(self, ticket_repo, spot_repo):
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo

    def execute(self, vehicle):
        ticket = self.ticket_repo.get_active_by_vehicle(vehicle.id)

        if not ticket:
            raise Exception(f"No hay ticket activo para la placa {vehicle.license_plate}")

        #(hora iniciada = hora cobrada)
        exit_time = timezone.now()
        duration = exit_time - ticket.entry_time
        horas_a_cobrar = math.ceil(duration.total_seconds() / 3600)
        
        if horas_a_cobrar <= 0:
            horas_a_cobrar = 1

        #Cálculo base
        total = horas_a_cobrar * self.TARIFA_UNICA

        #Descuento del 20% si no es "Visitante"
        if vehicle.client and vehicle.client.name.strip().lower() != "visitante":
            total = total * 0.80

        ticket.exit_time = exit_time
        ticket.total_paid = int(total)
        ticket.status = "CLOSED"
        self.ticket_repo.save(ticket)

        if ticket.parking_spot_id:
            self.spot_repo.free(ticket.parking_spot_id)

        return ticket.total_paid