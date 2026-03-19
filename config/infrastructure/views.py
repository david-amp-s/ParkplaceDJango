# infrastructure/views.py

from django.shortcuts import render, redirect
from domain.use_cases.login_user import LoginUser
from .repositories import DjangoUserRepository


import traceback

def login_view(request):
    print("METHOD:", request.method)

    if request.method == "GET":
        return render(request, "login.html")

    if request.method == "POST":
        print("POST DATA:", request.POST)

        username = request.POST.get("username")
        password = request.POST.get("password")

        print("USERNAME:", username)

        repo = DjangoUserRepository()
        use_case = LoginUser(repo)

        try:
            user = use_case.execute(username, password)
            print("LOGIN OK")

            request.session["user_id"] = user.id
            request.session["username"] = user.username
            request.session["role"] = user.role

            return redirect("/dashboard/")

        except Exception as e:
            print("ERROR EN LOGIN:")
            traceback.print_exc()  # 🔥 clave

            return render(request, "login.html", {
                "error": str(e)
            })
            
# infrastructure/views.py

def dashboard_view(request):

    if not request.session.get("user_id"):
        return redirect("/")

    return render(request, "dashboard.html", {
        "username": request.session.get("username")
    })
    
def logout_view(request):
    request.session.flush()
    return redirect("/")