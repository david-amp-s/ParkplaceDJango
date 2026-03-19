from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.parking_spot import ParkingSpot

class ParkingSpotRepository(ABC):
    
    @abstractmethod
    def get_all(self) -> List[ParkingSpot]:
        pass
    
    @abstractmethod
    def get_by_id(self, spot_id: int) -> Optional[ParkingSpot]:
        pass
    
    @abstractmethod
    def create (self, spot: ParkingSpot) -> ParkingSpot:
        pass
    
    @abstractmethod
    def update(self, spot: ParkingSpot) -> ParkingSpot:
        pass
    
    @abstractmethod
    def delete (self, spot_id: int) -> None: 
        pass
    
    @abstractmethod
    def number_exists(self, number: int, exclude_id: int = None) -> bool: 
        pass 
