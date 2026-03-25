from domain.entities.parking_spot import ParkingSpot
from domain.ports.parking_spot_repository import ParkingSpotRepository

class CreateParkingSpot:

    def __init__(self, repository: ParkingSpotRepository):
        self.repository = repository

    def execute(self, number: int) -> ParkingSpot:
        spot = ParkingSpot(id=None, number=number, status="AVAILABLE")
        return self.repository.save(spot)