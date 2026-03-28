from django.contrib.auth.hashers import check_password


class LoginUser:
    def __init__(self, employee_repository):
        self.employee_repository = employee_repository
    
    def execute(self, username , password) :
        employee = self.employee_repository.find_by_username(username)
        if not employee:
            raise Exception("Usuario no existe")
        if not check_password(password, employee.password):
            raise Exception("Credenciales invalidas")
        return employee