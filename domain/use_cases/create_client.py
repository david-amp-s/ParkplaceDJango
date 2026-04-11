from domain.entities.client import Client

class CreateClient:

    def __init__(self, repository):
        self.repository = repository

    def execute(self, name, phone, email, client_type='REGULAR'):
        client = Client(name, phone, email, client_type)
        return self.repository.save(client)