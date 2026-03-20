from domain.entities.vehicle import Vehicle

class CreateVehicle:

    def __init__(self, repository):
        self.repository = repository

    def execute(self, plate, type, client_id):
        vehicle = Vehicle(plate, type, client_id)
        return self.repository.save(vehicle)