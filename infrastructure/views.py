# infrastructure/views.py

from django.shortcuts import render, redirect
from domain.use_cases.login_user import LoginUser
from .repositories import DjangoUserRepository
from .repositories import DjangoClientRepository, DjangoVehicleRepository
from domain.use_cases.create_client import CreateClient
from domain.use_cases.create_vehicle import CreateVehicle


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

#Cliente

def create_client_view(request):

    if request.method == 'POST':
        name = request.POST['name']
        phone = request.POST['phone']
        email = request.POST.get('email')

        repo = DjangoClientRepository()
        use_case = CreateClient(repo)
        use_case.execute(name, phone, email)

        return redirect('/clientes/')

    return render(request, 'create_client.html')

def list_clients_view(request):
    from .models import Client

    clients = Client.objects.all()

    return render(request, 'list_clients.html', {
        'clients': clients
    })

#Vehiculo

from .models import Client

def create_vehicle_view(request):

    clients = Client.objects.all() 

    if request.method == 'POST':
        plate = request.POST['plate']
        type = request.POST['type']
        client_id = request.POST['client_id']

        repo = DjangoVehicleRepository()
        use_case = CreateVehicle(repo)
        use_case.execute(plate, type, client_id)

        return redirect('/vehiculos/create/')

    return render(request, 'create_vehicle.html', {
        'clients': clients 
    })

from .models import Vehicle

def list_vehicles_view(request):

    vehicles = Vehicle.objects.all()

    return render(request, 'list_vehicles.html', {
        'vehicles': vehicles
    })