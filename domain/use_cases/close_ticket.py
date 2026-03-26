from django.utils import timezone

class CloseTicket:

    RATES = {
        "CAR": 3000,
        "MOTORCYCLE": 1500,
        "BICYCLE": 500
    }

    def __init__(self, ticket_repo, spot_repo):
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo

    def execute(self, vehicle):

        from infrastructure.models import Ticket

        ticket = Ticket.objects.filter(
            vehicle_id=vehicle.id,
            status='ACTIVE'
        ).first()

        if not ticket:
            raise Exception("No hay ticket activo")

        # ⏱ Tiempo
        exit_time = timezone.now()
        duration = exit_time - ticket.entry_time

        hours = duration.total_seconds() / 3600
        hours = int(hours) + (1 if hours % 1 > 0 else 0)

        # 💰 Total
        total = hours * self.RATES[vehicle.type]

        # 🔒 Cerrar ticket
        ticket.exit_time = exit_time
        ticket.total_paid = total
        ticket.status = "CLOSED"

        self.ticket_repo.save(ticket)

        # 🅿️ Liberar espacio
        self.spot_repo.free(ticket.parking_spot_id)

        return total