from abc import ABC, abstractmethod
from domain.entities.parking_spot import ParkingSpot

class ParkingSpotRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[ParkingSpot]:
        pass

    @abstractmethod
    def get_by_id(self, spot_id: int) -> ParkingSpot:
        pass

    @abstractmethod
    def save(self, parking_spot: ParkingSpot) -> ParkingSpot:
        pass

    @abstractmethod
    def update(self, parking_spot: ParkingSpot) -> ParkingSpot:
        pass