class Payment:
    def __init__(self, ticket_id, method, amount, employee_id=None):
        self.ticket_id = ticket_id
        self.method = method
        self.amount = amount
        self.employee_id = employee_id