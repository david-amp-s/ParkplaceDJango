# domain/use_cases/get_history.py

class GetHistory:
    def __init__(self, ticket_repository):
        self.ticket_repository = ticket_repository

    def execute(self):
        return self.ticket_repository.get_history_all()