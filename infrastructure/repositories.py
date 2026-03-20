from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from .models import AppUser
from .models import Client, Vehicle

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