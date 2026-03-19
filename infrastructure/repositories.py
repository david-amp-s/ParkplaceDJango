from domain.entities.user import User
from domain.ports.user_repository import UserRepository
from .models import AppUser
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
        
class DjangoPaymentRepository:
    def save(self, payment):
        return PaymentModel.objects.create(
            ticket_id = payment.ticket_id,
            employee_id = payment.employee_id,
            method = payment.method,
            amount = payment.amount
        )