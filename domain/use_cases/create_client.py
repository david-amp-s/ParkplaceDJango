from domain.entities.client import Client

class CreateClient:

    def __init__(self, repository):
        self.repository = repository

    def execute(self, name, phone, email):
        client = Client(name, phone, email)
        return self.repository.save(client)