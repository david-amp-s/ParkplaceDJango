from datetime import timezone

from infrastructure.models import Ticket

class PayticketUseCase:

   def __init__(self, payment_repository):
     self.payment_repository = payment_repository

   def execute(self, ticket_id, method, amount, employee_id=None):

     ticket = Ticket.objects.get(id=ticket_id)

     if ticket.status != 'ACTIVE':
      raise Exception("El ticket ya está cerrado")

     #Guardar pago
     payment = self.payment_repository.save({
     "ticket_id": ticket_id,
     "method": method,
     "amount": amount,
     "employee_id": employee_id
     })

     #Cerrar ticket
     ticket.status = 'CLOSED'
     ticket.total_paid = amount
     ticket.exit_time = timezone.now()
     ticket.save()

     return payment
