from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SpotType(str, Enum):
    CAR = "CAR"
    MOTORCYCLE = "MOTORCYCLE"
    
class SpotStatus (str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
    
@dataclass
class ParkingSpot: 
    number: int
    type: SpotType
    status: SpotStatus
    id: int = None
    created_at: datetime = None    