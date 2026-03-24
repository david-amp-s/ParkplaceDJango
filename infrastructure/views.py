import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Vehicle, Client as ClientModel
from .repositories import (
    DjangoUserRepository, DjangoClientRepository, 
    DjangoVehicleRepository, DjangoPaymentRepository
)
from domain.entities.client import Client
from domain.entities.vehicle import Vehicle as VehicleEntity
from domain.use_cases.login_user import LoginUser
from domain.use_cases.create_client import CreateClient
from domain.use_cases.create_vehicle import CreateVehicle
from domain.use_cases.pay_ticket import PayticketUseCase

#Autenticacion
def login_view(request):
    if request.method == "GET":
        return render(request, "login.html")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        repo = DjangoUserRepository()
        use_case = LoginUser(repo)
        try:
            user = use_case.execute(username, password)
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            request.session["role"] = user.role
            return redirect("/dashboard/")
        except Exception as e:
            traceback.print_exc()
            return render(request, "login.html", {"error": str(e)})

#Panel principal
def dashboard_view(request):
    return render(request, "dashboard.html")

#Cierre de sesion
def logout_view(request):
    request.session.flush()
    return redirect("/")

#Gestion de clientes
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
    return render(request, 'list_clients.html', {'clients': clients})

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

#Gestion de vehiculos
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
    return render(request, 'create_vehicle.html', {'clients': clients})

def list_vehicles_view(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'list_vehicles.html', {'vehicles': vehicles})

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

#Registro de entrada
def entry_vehicle_view(request):
    from infrastructure.models import Client, Vehicle
    from .repositories import DjangoTicketRepository, DjangoParkingSpotRepository
    from domain.use_cases.create_ticket import CreateTicket

    if request.method == 'POST':
        plate_text = request.POST.get('license_plate', '').strip().upper()
        if not plate_text:
            return render(request, 'entry_vehicle.html', {'error': 'La placa es obligatoria'})
        cliente_gen, _ = Client.objects.get_or_create(
            name="Visitante", 
            defaults={'phone': '000'}
        )
        vehiculo_obj, _ = Vehicle.objects.get_or_create(
            license_plate=plate_text,
            defaults={'client': cliente_gen, 'type': 'CAR'}
        )
        ticket_repo = DjangoTicketRepository()
        spot_repo = DjangoParkingSpotRepository()
        use_case = CreateTicket(ticket_repo, spot_repo)

        try:
            use_case.execute(vehiculo_obj.id, None)
            messages.success(request, f"Ingreso exitoso: {plate_text}")
        except Exception as e:
            return render(request, 'entry_vehicle.html', {'error': str(e)})

    return render(request, 'entry_vehicle.html')

#Registro de salida
def exit_vehicle_view(request):
    from infrastructure.models import Ticket
    from domain.use_cases import close_ticket as close_ticket_module
    from .repositories import DjangoTicketRepository, DjangoParkingSpotRepository

    if request.method == 'POST':
        plate_text = request.POST.get('license_plate', '').strip().upper()
        try:
            vehicle = Vehicle.objects.get(license_plate=plate_text)
            ticket_activo = Ticket.objects.filter(vehicle=vehicle, status='ACTIVE').first()
            if not ticket_activo:
                messages.error(request, f"El vehiculo {plate_text} no tiene ingreso activo")
                return redirect('/salida/')
            ticket_repo = DjangoTicketRepository()
            spot_repo = DjangoParkingSpotRepository()
            try:
                use_case = close_ticket_module.CloseTicket(ticket_repo, spot_repo)
            except AttributeError:
                use_case = close_ticket_module.close_ticket(ticket_repo, spot_repo)
            total = use_case.execute(vehicle)
            messages.success(request, f"Salida procesada - Placa: {plate_text} - Total: ${total}")
        except Vehicle.DoesNotExist:
            messages.error(request, f"La placa {plate_text} no existe")
            return redirect('/salida/')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('/salida/')
    return render(request, 'exit_vehicle.html')

#Registro de pagos
def pay_ticket_view(request):
    if request.method == "POST":
        try:
            ticket_id = request.POST['ticket_id']
            method = request.POST['method']
            amount = request.POST['amount']
            employee_id = request.session.get('user_id')
            use_case = PayticketUseCase(DjangoPaymentRepository())
            use_case.execute(ticket_id, method, amount, employee_id)
            return redirect('/dashboard/')
        except Exception as e:
            return render(request, "pay_ticket.html", {"error": str(e)})
    return render(request, "pay_ticket.html")