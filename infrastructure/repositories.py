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


class DjangoClientRepository:

    def save(self, data):
        return Client.objects.create(**data)

    def get_all(self):
        return Client.objects.all()


class DjangoVehicleRepository:

    def save(self, data):
        return Vehicle.objects.create(**data)