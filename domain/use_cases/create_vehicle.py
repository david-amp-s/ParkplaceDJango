# domain/use_cases/create_vehicle.py

class CreateVehicle:
    def __init__(self, vehicle_repository):
        self.vehicle_repository = vehicle_repository

    def execute(self, plate, v_type, client_id):
        return self.vehicle_repository.save(plate, v_type, client_id)