class CreateClient:

    def __init__(self, repository):
        self.repository = repository

    def execute(self, name, phone, email):
        return self.repository.save({
            "name": name,
            "phone": phone,
            "email": email
        })