# ASÍ DEBE ESTAR
class Vehicle:
    def __init__(self, license_plate, type, client_id):
        self.license_plate = license_plate
        # Asegúrate de que NO diga self.type = "CARRO"
        self.type = type  
        self.client_id = client_id