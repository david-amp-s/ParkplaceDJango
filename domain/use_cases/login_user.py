from django.contrib.auth.hashers import check_password


class LoginUser:
    def __init__(self, user_repo):
        self.user_repo = user_repo
    
    def execute(self, username , password) :
        user = self.user_repo.find_by_username(username)
        if not user:
            raise Exception("Usuario no existe")
        if not user.is_active:
            raise Exception("Usuario inactivo")
        if not check_password(password, user.password):
            raise Exception("Credenciales invalidas")
        return user