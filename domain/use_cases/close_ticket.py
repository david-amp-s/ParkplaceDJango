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

        ticket = Ticket.objects.filter(vehicle_id=vehicle.id, status='ACTIVE').first()

        if not ticket:
            raise Exception("No hay ticket activo para este vehículo")

        exit_time = timezone.now()
        entry_time = ticket.entry_time
        duration = exit_time - entry_time
        seconds = duration.total_seconds()
        
        hours = seconds / 3600

        #al menos 1 hora
        hours_to_charge = int(hours) + (1 if (seconds % 3600) > 0 else 0)

        if hours_to_charge <= 0:
            hours_to_charge = 1

        #Obtener la tarifa base según el tipo de vehículo
        base_rate = self.RATES.get(vehicle.type, 3000)

        # 2. LÓGICA DE CLIENTE REGISTRADO
        # Si el nombre del cliente NO es "Visitante", aplicamos descuento
        if vehicle.client and vehicle.client.name != "Visitante":
            base_rate = base_rate * 0.8 
            print(f"DEBUG: Aplicando descuento a cliente registrado: {vehicle.client.name}")

        # 3. Calcular el total final
        total = int(hours_to_charge * base_rate)

        # Actualiza el ticket
        ticket.exit_time = exit_time
        ticket.total_paid = total
        ticket.status = "CLOSED"

        # Guarda
        ticket.save() 
        
        # Libera el espacio
        self.spot_repo.free(ticket.parking_spot_id)

        return total