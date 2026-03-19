from typing import List, Optional
from domain.entities.parking_spot import ParkingSpot, SpotStatus, SpotType
from domain.ports.parking_spot_repository import ParkingSpotRepository

class GetAllParkingSpotsUseCase:
    def __init__(self, repository: ParkingSpotRepository):
        self.repository = repository
        
    def execute(self) -> List[ParkingSpot]:
        return self.repository.get_all()
    
class GetParkingSportByIdUseCase: 
    def __init__(self,repository: ParkingSpotRepository):
        self.repository = repository
        
    def execute(self, spot_id: int) -> Optional[ParkingSpot]:
        spot = self.repository.get_by_id(spot_id)
        if not spot:
            raise ValueError(F"Parking spot with id {spot_id} not found.")
        return spot
    
class CreateParkingSpotUseCase: 
    def __init__(self, repository: ParkingSpotRepository):
        self.repository = repository 
        
    def execute(self, number: int, type: str, status: str = "AVAILABLE") -> ParkingSpot:
        if self.repository.number_exists(number):
            raise ValueError (f"A parking spot with number {number} already exists.")
        
        spot = ParkingSpot(
            number=number,
            type=SpotType(type),
            status=SpotStatus(status),
        )
        return self.repository.create(spot)
    
class UpdateParkingSpotUseCase:
    def __init__(self, repository: ParkingSpotRepository):
        self.repository = repository
        
    def execute(self, spot_id: int, number: int, type: str, status: str) -> ParkingSpot:
        existing = self.repository.get_by_id(spot_id)
        if not existing:
            raise ValueError(f"A parking spot with id {spot_id} not found.")
        
        if self.repository.number_exists(number, exclude_id=spot_id):
            raise ValueError(f"A parking spot with number {number} already exists.")
        
        
        existing.number = number
        existing.type = SpotStatus(type)
        existing.status = SpotStatus(status)
        
        return self.repository.update(existing)
    
class DeleteParkingSpotUseCase: 
    def __init__(self, repository: ParkingSpotRepository):
        self.reposirtory = repository
        
    def execute(self, spot_id: int) -> None:
        existing = self.reposirtory.get_by_id(spot_id)
        if not existing:
            raise ValueError(f"Parking spot with id {sport_id} not found.")
        self.reposirtory.delete(spot_id)