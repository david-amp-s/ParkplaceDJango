from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from .models import AppUser
from .models import Client, Vehicle
from .models import Ticket, ParkingSpot
from .models import Payment as PaymentModel

class DjangoUserRepository(UserRepository):
    def find_by_username(self,username):
        try : 
            user = AppUser.objects.get(username=username)
            return User(
                id = user.id,
                username = user.username,
                password = user.password,
                role = user.role,
                is_active = user.is_active
            )
        except AppUser.DoesNotExist :
            return None



from .models import Client as ClientModel

class DjangoClientRepository:

    def save(self, client):
        return ClientModel.objects.create(
            name=client.name,
            phone=client.phone,
            email=client.email
        )

    def get_all(self):
        return ClientModel.objects.all()


from .models import Vehicle as VehicleModel

class DjangoVehicleRepository:

    def save(self, vehicle):
        return VehicleModel.objects.create(
            license_plate=vehicle.license_plate,
            type=vehicle.type,
            client_id=vehicle.client_id
        )




class DjangoTicketRepository:

    def create(self, data):
        data.pop('employee_id', None)  # temporal mientras karlos termino lo suyo
        return Ticket.objects.create(**data)

    def get_active_by_vehicle(self, vehicle_id):
        return Ticket.objects.filter(
            vehicle_id=vehicle_id,
            status='ACTIVE'
        ).first()

    def save(self, ticket):
        ticket.save()
        return ticket


class DjangoParkingSpotRepository:

    def get_available(self):
        return ParkingSpot.objects.filter(status='AVAILABLE').first()

    def occupy(self, spot_id):
        spot = ParkingSpot.objects.get(id=spot_id)
        spot.status = 'OCCUPIED'
        spot.save()

    def free(self, spot_id):
        spot = ParkingSpot.objects.get(id=spot_id)
        spot.status = 'AVAILABLE'
        spot.save()


        
class DjangoPaymentRepository:
    def save(self, payment):
        return PaymentModel.objects.create(
            ticket_id = payment.ticket_id,
            employee_id = payment.employee_id,
            method = payment.method,
            amount = payment.amount
        )
