class CreateVehicle:

    def __init__(self, repository):
        self.repository = repository

    def execute(self, plate, type, client_id):
        return self.repository.save({
            "license_plate": plate,
            "type": type,
            "client_id": client_id
        })