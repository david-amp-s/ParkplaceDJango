from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from .models import AppUser
from .models import Client, Vehicle
from .models import Ticket, ParkingSpot
from .models import Payment as PaymentModel

from domain.entities.employee import Employee
from domain.ports.employee_repository import EmployeeRepository
from infrastructure.models import Employee, AppUser


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


class DjangoEmployeeRepository(EmployeeRepository):

    def get_all(self):
        return [
            Employee(e.id, e.user.id, e.name, e.phone)
            for e in Employee.objects.select_related('user').all()
        ]

    def get_by_id(self, employee_id):
        e = Employee.objects.select_related('user').get(id=employee_id)
        return Employee(e.id, e.user.id, e.name, e.phone)

    def create(self, employee):
        user = AppUser.objects.get(id=employee.user_id)

        e = Employee.objects.create(
            user=user,
            name=employee.name,
            phone=employee.phone
        )

        return Employee(e.id, e.user.id, e.name, e.phone)

    def delete(self, employee_id):
        Employee.objects.get(id=employee_id).delete()


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
        return spot

    def free(self, spot_id):
        spot = ParkingSpot.objects.get(id=spot_id)
        spot.status = 'AVAILABLE'
        spot.save()
        return spot

    def get_all(self):
        return ParkingSpot.objects.all()

    def get_by_id(self, spot_id):
        return ParkingSpot.objects.get(id=spot_id)

    def save(self, data):
        return ParkingSpot.objects.create(**data)

    def update(self, spot):
        spot.save()
        return spot


        
class DjangoPaymentRepository:
    def save(self, payment):
        return PaymentModel.objects.create(
            ticket_id = payment.ticket_id,
            employee_id = payment.employee_id,
            method = payment.method,
            amount = payment.amount
        )
