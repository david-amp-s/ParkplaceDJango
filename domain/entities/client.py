class Client:
    def __init__(self, name, phone, email=None, client_type='REGULAR'):
        self.name = name
        self.phone = phone
        self.email = email
        self.client_type = client_type