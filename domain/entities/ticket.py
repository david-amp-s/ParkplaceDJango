class Ticket:
    def __init__(self, vehicle_id, parking_spot_id, employee_id, entry_time):
        self.vehicle_id = vehicle_id
        self.parking_spot_id = parking_spot_id
        self.employee_id = employee_id
        self.entry_time = entry_time
        self.status = "ACTIVE"