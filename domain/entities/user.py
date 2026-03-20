class User:
    def __init__(self,id,username,password,role,is_active =True):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.is_active = is_active

