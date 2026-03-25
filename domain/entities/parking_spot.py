class ParkingSpot:
    def __init__(self, id: int, number: int, status: str = "AVAILABLE", type: str = "CAR"):
        self.id = id
        self.number = number
        self.status = status
        self.type = type

    def occupy(self):
        self.status = "OCCUPIED"

    def release(self):
        self.status = "AVAILABLE"