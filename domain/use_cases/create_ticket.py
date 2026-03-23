from datetime import datetime

class CreateTicket:

    def __init__(self, ticket_repo, spot_repo):
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo

    def execute(self, vehicle_id, employee_id):

        #buscar espacio
        spot = self.spot_repo.get_available()

        if not spot:
            raise Exception("No hay espacios disponibles")

        #crear
        ticket = {
            "vehicle_id": vehicle_id,
            "parking_spot_id": spot.id,
            "employee_id": employee_id,
            "entry_time": datetime.now(),
            "status": "ACTIVE"
        }

        self.ticket_repo.create(ticket)

        #actualizar
        self.spot_repo.occupy(spot.id)