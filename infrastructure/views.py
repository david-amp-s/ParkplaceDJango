from django.shortcuts import render, redirect, get_object_or_404
from domain.use_cases.login_user import LoginUser
from .repositories import DjangoUserRepository
from .repositories import DjangoClientRepository, DjangoVehicleRepository
from domain.use_cases.create_client import CreateClient
from domain.use_cases.create_vehicle import CreateVehicle

from .models import Vehicle
from .models import Client as ClientModel 

from domain.entities.client import Client
from domain.entities.vehicle import Vehicle as VehicleEntity
from .models import Client as ClientModel

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
            traceback.print_exc()

            return render(request, "login.html", {
                "error": str(e)
            })


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

    clients = ClientModel.objects.all()

    return render(request, 'list_clients.html', {
        'clients': clients
    })


def edit_client_view(request, id):

    client_model = get_object_or_404(ClientModel, id=id)

    if request.method == 'POST':
        entity = Client(
            request.POST['name'],
            request.POST['phone'],
            request.POST.get('email')
        )

        client_model.name = entity.name
        client_model.phone = entity.phone
        client_model.email = entity.email
        client_model.save()

        return redirect('/clientes/')

    return render(request, 'edit_client.html', {'client': client_model})

#Vehiculo

def create_vehicle_view(request):

    if request.method == 'POST':
        plate = request.POST['plate']
        type = request.POST['type']
        client_id = request.POST.get('client_id')

        repo = DjangoVehicleRepository()
        use_case = CreateVehicle(repo)
        use_case.execute(plate, type, client_id)

        return redirect('/vehiculos/')

    clients = ClientModel.objects.all()

    return render(request, 'create_vehicle.html', {
        'clients': clients
    })

def list_vehicles_view(request):

    vehicles = Vehicle.objects.all()

    return render(request, 'list_vehicles.html', {
        'vehicles': vehicles
    })


def edit_vehicle_view(request, id):

    vehicle_model = get_object_or_404(Vehicle, id=id)

    if request.method == 'POST':
        entity = VehicleEntity(
            request.POST['plate'],
            request.POST['type'],
            request.POST['client_id']
        )

        vehicle_model.license_plate = entity.license_plate
        vehicle_model.type = entity.type
        vehicle_model.client_id = entity.client_id
        vehicle_model.save()

        return redirect('/vehiculos/')

    return render(request, 'edit_vehicle.html', {'vehicle': vehicle_model})



#DELETE 

# def delete_client_view(request, id):
#     client = get_object_or_404(ClientModel, id=id)
#     client.delete()
#     return redirect('/clientes/')


# def delete_vehicle_view(request, id):
#     vehicle = get_object_or_404(Vehicle, id=id)
#     vehicle.delete()
#     return redirect('/vehiculos/')

#TICKET

def entry_vehicle_view(request):

    from .models import Vehicle
    from .repositories import DjangoTicketRepository, DjangoParkingSpotRepository
    from domain.use_cases.create_ticket import CreateTicket

    if request.method == 'POST':
        vehicle_id = request.POST['vehicle_id']
        employee_id = 1  # temporal

        ticket_repo = DjangoTicketRepository()
        spot_repo = DjangoParkingSpotRepository()

        use_case = CreateTicket(ticket_repo, spot_repo)
        use_case.execute(vehicle_id, None) #Meter empleado cuando Karlos haga la función

        return redirect('/dashboard/')

    vehicles = Vehicle.objects.all()

    return render(request, 'entry_vehicle.html', {
        'vehicles': vehicles

    })

def exit_vehicle_view(request):

    from infrastructure.models import Vehicle
    from domain.use_cases.close_ticket import CloseTicket
    from .repositories import DjangoTicketRepository, DjangoParkingSpotRepository

    if request.method == 'POST':
        vehicle_id = request.POST.get('vehicle_id')

        print("VEHICLE ID:", vehicle_id)

        vehicle = Vehicle.objects.get(id=vehicle_id)

        ticket_repo = DjangoTicketRepository()
        spot_repo = DjangoParkingSpotRepository()

        use_case = CloseTicket(ticket_repo, spot_repo)

        total = use_case.execute(vehicle)

        print("TOTAL:", total)

        return render(request, "ok.html", {
            "mensaje": f"Salida OK - Total: {total}"
        })

    vehicles = Vehicle.objects.all()

    return render(request, 'exit_vehicle.html', {
        'vehicles': vehicles
    })