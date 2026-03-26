from datetime import datetime

class CreateTicket:

    def __init__(self, ticket_repo, spot_repo):
        self.ticket_repo = ticket_repo
        self.spot_repo = spot_repo

    def execute(self, vehicle_id, employee_id):

        # 🚫 EVITAR DOBLE INGRESO
        existing_ticket = self.ticket_repo.get_active_by_vehicle(vehicle_id)

        if existing_ticket:
            raise Exception("El vehículo ya está dentro del parqueadero")

        # 🔍 Buscar espacio disponible
        spot = self.spot_repo.get_available()

        if not spot:
            raise Exception("No hay espacios disponibles")

        # 🅿️ Ocupar espacio
        spot.occupy()   # 🔥 YA GUARDA SOLO

        # 🎫 Crear ticket
        ticket_data = {
            "vehicle_id": vehicle_id,
            "parking_spot_id": spot.id,
            "employee_id": employee_id,
            "entry_time": datetime.now(),
            "status": "ACTIVE"
        }

        self.ticket_repo.create(ticket_data)

