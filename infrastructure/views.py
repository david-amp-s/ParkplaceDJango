import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Vehicle, Client, AppUser, Ticket
from .repositories import (
    DjangoUserRepository, DjangoClientRepository, 
    DjangoVehicleRepository, DjangoPaymentRepository,
    DjangoEmployeeRepository, DjangoTicketRepository, 
    DjangoParkingSpotRepository
)

from domain.entities.employee import Employee
from domain.use_cases.login_user import LoginUser
from domain.use_cases.create_client import CreateClient
from domain.use_cases.create_vehicle import CreateVehicle
from domain.use_cases.pay_ticket import PayticketUseCase
from domain.use_cases.create_ticket import CreateTicket
from domain.use_cases.get_history import GetHistory
from domain.use_cases import close_ticket as close_ticket_module


#AUTENTICACIÓN Y PANEL

def login_view(request):
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
    return render(request, "login.html")

def dashboard_view(request):
    return render(request, "dashboard.html")

def logout_view(request):
    request.session.flush()
    return redirect("/")

#GESTIÓN DE EMPLEADOS

def list_employees(request):
    repo = DjangoEmployeeRepository()
    employees = repo.get_all()
    return render(request, "list_employees.html", {"employees": employees})

def create_employee(request):
    if request.method == "POST":
        user = AppUser.objects.create(
            username=request.POST["username"],
            password=request.POST["password"],  
            role="EMPLOYEE"
        )
        employee = Employee(
            id=None,
            user_id=user.id,
            name=request.POST["name"],
            phone=request.POST["phone"]
        )
        repo = DjangoEmployeeRepository()
        repo.create(employee)
        return redirect("/employee/")
    return render(request, "create_employee.html")

#GESTIÓN DE CLIENTES

def list_clients_view(request):
    clients = Client.objects.all().order_by('id')
    return render(request, 'list_clients.html', {'clients': clients})

def create_client_view(request):
    if request.method == 'POST':
        repo = DjangoClientRepository()
        use_case = CreateClient(repo)
        use_case.execute(
            request.POST['name'], 
            request.POST['phone'], 
            request.POST.get('email')
        )
        return redirect('/clientes/')
    return render(request, 'create_client.html')

def edit_client_view(request, id):
    client_obj = get_object_or_404(Client, id=id)
    if request.method == 'POST':
        client_obj.name = request.POST['name']
        client_obj.phone = request.POST['phone']
        client_obj.email = request.POST.get('email')
        client_obj.save()
        return redirect('/clientes/')
    return render(request, 'edit_client.html', {'client': client_obj})

def delete_client_view(request, id):
    client_obj = get_object_or_404(Client, id=id)
    if request.method == 'POST':
        client_obj.delete() 
        messages.success(request, f"Cliente {client_obj.name} eliminado.")
        return redirect('/clientes/')
    return render(request, 'delete_client.html', {'client': client_obj})

#GESTIÓN DE VEHÍCULOS 

def list_vehicles_view(request):
    vehicles = Vehicle.objects.all().order_by('id')
    return render(request, 'list_vehicles.html', {'vehicles': vehicles})

def create_vehicle_view(request):
    if request.method == 'POST':
        repo = DjangoVehicleRepository()
        use_case = CreateVehicle(repo)
        use_case.execute(
            request.POST['plate'].upper(), 
            request.POST['type'], 
            request.POST.get('client_id')
        )
        return redirect('/vehiculos/')
    clients = Client.objects.all()
    return render(request, 'create_vehicle.html', {'clients': clients})

def edit_vehicle_view(request, id):
    vehicle_obj = get_object_or_404(Vehicle, id=id)
    if request.method == 'POST':
        vehicle_obj.license_plate = request.POST['plate'].upper()
        vehicle_obj.type = request.POST['type']
        vehicle_obj.client_id = request.POST['client_id']
        vehicle_obj.save()
        return redirect('/vehiculos/')
    clients = Client.objects.all()
    return render(request, 'edit_vehicle.html', {'vehicle': vehicle_obj, 'clients': clients})

def delete_vehicle_view(request, id):
    vehicle_obj = get_object_or_404(Vehicle, id=id)
    if request.method == 'POST':
        vehicle_obj.delete()
        return redirect('/vehiculos/')
    return render(request, 'delete_vehicle.html', {'vehicle': vehicle_obj})

#OPERACIONES DE PARQUEADERO

def entry_vehicle_view(request):
    if request.method == 'POST':
        plate_text = request.POST.get('license_plate', '').strip().upper()
        vehicle_type = request.POST.get('vehicle_type', 'CAR') 

        if not plate_text:
            return render(request, 'entry_vehicle.html', {'error': 'La placa es obligatoria'})

        cliente_gen, _ = Client.objects.get_or_create(
            name="Visitante", defaults={'phone': '000'}
        )
        vehiculo_obj, created = Vehicle.objects.get_or_create(
            license_plate=plate_text,
            defaults={'client': cliente_gen, 'type': vehicle_type}
        )
        
        if not created and vehiculo_obj.type != vehicle_type:
             vehiculo_obj.type = vehicle_type
             vehiculo_obj.save()

        use_case = CreateTicket(DjangoTicketRepository(), DjangoParkingSpotRepository())
        try:
            use_case.execute(vehiculo_obj.id, None)  
            messages.success(request, f"✅ Ingreso: {plate_text}")
            return redirect('/ingreso/')
        except Exception as e:
            return render(request, 'entry_vehicle.html', {'error': str(e)})
    return render(request, 'entry_vehicle.html')

def exit_vehicle_view(request):
    if request.method == 'POST':
        plate_text = request.POST.get('license_plate', '').strip().upper()
        try:
            vehicle_obj = Vehicle.objects.get(license_plate=plate_text)
            ticket_repo = DjangoTicketRepository()
            spot_repo = DjangoParkingSpotRepository()
            
            try:
                use_case = close_ticket_module.CloseTicket(ticket_repo, spot_repo)
            except AttributeError:
                use_case = close_ticket_module.close_ticket(ticket_repo, spot_repo)
            
            total = use_case.execute(vehicle_obj)
            messages.success(request, f"Salida procesada - Total: ${total}")
            return redirect('/salida/')
        except Vehicle.DoesNotExist:
            messages.error(request, f"La placa {plate_text} no existe")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    return render(request, 'exit_vehicle.html')

#PAGOS E HISTORIAL

def pay_ticket_view(request):
    if request.method == "POST":
        try:
            use_case = PayticketUseCase(DjangoPaymentRepository())
            use_case.execute(
                request.POST['ticket_id'], 
                request.POST['method'], 
                request.POST['amount'], 
                request.session.get('user_id')
            )
            return redirect('/dashboard/')
        except Exception as e:
            return render(request, "pay_ticket.html", {"error": str(e)})
    return render(request, "pay_ticket.html")

def history_view(request):
    query = request.GET.get('q') 
    repo = DjangoTicketRepository()
    if query:
        tickets = repo.filter_by_plate(query)
    else:
        use_case = GetHistory(repo)
        tickets = use_case.execute()
    return render(request, 'list_history.html', {'tickets': tickets})