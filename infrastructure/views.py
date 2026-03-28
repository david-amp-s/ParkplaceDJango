import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

#Modelos de Infraestructura
from .models import ParkingSpot, Vehicle, Client as ClientModel, AppUser, Ticket

#Repositorios 
from .repositories import (
    DjangoUserRepository, DjangoClientRepository, 
    DjangoVehicleRepository, DjangoPaymentRepository,
    DjangoEmployeeRepository, DjangoTicketRepository, 
    DjangoParkingSpotRepository
)

#Entidades de Dominio
from domain.entities.employee import Employee
from domain.entities.client import Client as ClientEntity
from domain.entities.vehicle import Vehicle as VehicleEntity

from .repositories import DjangoParkingSpotRepository

#Casos de Uso
from domain.use_cases.login_user import LoginUser
from domain.use_cases.create_client import CreateClient
from domain.use_cases.create_vehicle import CreateVehicle
from domain.use_cases.pay_ticket import PayticketUseCase
from domain.use_cases.create_ticket import CreateTicket
from domain.use_cases.get_history import GetHistory
from domain.use_cases.close_ticket import CloseTicket

#AUTENTICACIÓN Y LOGOUT

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

def logout_view(request):
    request.session.flush()
    return redirect("/")

#DASHBOARD Y ESPACIOS

from django.db.models import DecimalField
from django.db.models.functions import Coalesce
from django.db.models import Value

from django.utils.timezone import now
from django.db.models import Sum, Count, DecimalField, Value
from django.db.models.functions import Coalesce

from django.db.models import Count
from django.utils.timezone import now

from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import Coalesce

def dashboard_view(request):

    #Espacios
    total = ParkingSpot.objects.count()
    available = ParkingSpot.objects.filter(status="AVAILABLE").count()
    occupied = ParkingSpot.objects.filter(status="OCCUPIED").count()
    ocupacion = int((occupied / total) * 100) if total > 0 else 0

    hoy = now().date()

    #Vehículos hoy
    vehiculos_hoy = Ticket.objects.filter(
        created_at__date=hoy
    ).count()

    #Ingresos hoy
    ingresos_hoy = Ticket.objects.filter(
        exit_time__date=hoy,
        status="CLOSED"
    ).aggregate(
        total=Coalesce(
            Sum("total_paid"),
            0,
            output_field=DecimalField()
        )
    )["total"]

    #Actividad reciente
    actividades = (
        Ticket.objects
        .select_related("vehicle")
        .only("status", "created_at", "vehicle__license_plate")
        .order_by("-created_at")[:5]
    )

    #Vehículos por tipo HOY (CORRECTO)
    vehiculos_por_tipo = (
        Ticket.objects
        .filter(created_at__date=hoy)
        .values("vehicle__type")
        .annotate(total=Count("id"))
    )

    #Listas limpias para JS
    tipos = [v["vehicle__type"] for v in vehiculos_por_tipo]
    cantidades = [v["total"] for v in vehiculos_por_tipo]

    #Insight automático
    insight = None
    conteo = {v["vehicle__type"]: v["total"] for v in vehiculos_por_tipo}

    carros = conteo.get("CAR", 0)
    motos = conteo.get("MOTORCYCLE", 0)

    if carros > motos:
        insight = f"🚗 Hoy han entrado más carros ({carros}) que motos ({motos})"
    elif motos > carros:
        insight = f"🏍️ Hoy han entrado más motos ({motos}) que carros ({carros})"
    elif carros == motos and carros > 0:
        insight = f"⚖️ Hoy hay igual número de carros y motos ({carros})"
    else:
        insight = "Sin datos suficientes hoy"

    #Clientes frecuentes (TOP 5)
    clientes_frecuentes = (
        Ticket.objects
        .values("vehicle__client__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    return render(request, "dashboard.html", {
        "ocupacion_actual": ocupacion,
        "vehiculos_hoy": vehiculos_hoy,
        "ingresos_hoy": ingresos_hoy,
        "actividades_recientes": actividades,
        "tipos": tipos,
        "cantidades": cantidades,
        "insight": insight,
        "clientes_frecuentes": clientes_frecuentes
    })

def parking_status_view(request):
    repo = DjangoParkingSpotRepository()
    all_spots_from_db = repo.get_all() 
    
    spots_with_info = []

    #Procesamos cada espacio para ver si tiene ticket
    for spot in all_spots_from_db:
        ticket = None
        is_occupied = (spot.status == "OCCUPIED")
        
        if is_occupied:
            #Buscamos el ticket activo solo si el spot dice que está ocupado
            ticket = Ticket.objects.filter(parking_spot=spot, status='ACTIVE').first()
        
        spots_with_info.append({
            "spot": spot, 
            "ticket": ticket,
            "is_occupied": is_occupied
        })

    return render(request, "parking_status.html", {
        "all_spots": spots_with_info 
    })

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
    clients = ClientModel.objects.all().order_by('id')
    return render(request, 'list_clients.html', {'clients': clients})

from .forms import ClientForm

from .forms import ClientForm

from .forms import ClientForm

def create_client_view(request):
    form = ClientForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            
            repo = DjangoClientRepository()
            use_case = CreateClient(repo)
            
            use_case.execute(
                data['name'], 
                data['phone'], 
                data.get('email')
            )

            messages.success(request, "Cliente creado correctamente")
            return redirect('/clientes/')
        else:
            messages.error(request, "Error en el formulario")

    return render(request, 'create_client.html', {
        'form': form
    })
            

from .forms import ClientForm

def edit_client_view(request, id):
    client_obj = get_object_or_404(ClientModel, id=id)
    
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():

            data = form.cleaned_data
            client_obj.name = data['name']
            client_obj.phone = data['phone']
            client_obj.email = data.get('email')
            
            #Actualizamos también el tipo de cliente
            client_obj.client_type = data['client_type'] 
            
            client_obj.save()
            return redirect('/clientes/')
        else:

            print(f"Errores en el formulario: {form.errors}")
    else:
        form = ClientForm(initial={
            'name': client_obj.name,
            'phone': client_obj.phone,
            'email': client_obj.email,
            'client_type': getattr(client_obj, 'client_type', 'REGULAR')
        })

    return render(request, 'edit_client.html', {'form': form, 'client': client_obj})


def delete_client_view(request, id):
    client_obj = get_object_or_404(ClientModel, id=id)
    if request.method == 'POST':
        client_obj.delete() 
        messages.success(request, f"Cliente {client_obj.name} eliminado.")
        return redirect('/clientes/')
    return render(request, 'delete_client.html', {'client': client_obj})

#GESTIÓN DE VEHÍCULOS

def list_vehicles_view(request):
    vehicles = Vehicle.objects.all().order_by('id')
    return render(request, 'list_vehicles.html', {'vehicles': vehicles})

from django.db import IntegrityError

def create_vehicle_view(request):
    if request.method == 'POST':
        plate = request.POST.get('plate', '').strip().upper()
        vehicle_type = request.POST.get('type')
        client_id = request.POST.get('client_id')

        #(El filtro de seguridad) 
        if len(plate) > 6:
            clients = ClientModel.objects.all()
            return render(request, 'create_vehicle.html', {
                'clients': clients,
                'error': f"La placa '{plate}' es demasiado larga. El máximo permitido son 6 caracteres."
            })

        repo = DjangoVehicleRepository()
        use_case = CreateVehicle(repo)

        try:
            use_case.execute(plate, vehicle_type, client_id)
            messages.success(request, "Vehículo registrado exitosamente.")
            return redirect('/vehiculos/')
        except IntegrityError:
            clients = ClientModel.objects.all()
            return render(request, 'create_vehicle.html', {
                'clients': clients,
                'error': f"El vehículo con placa {plate} ya está registrado."
            })
        except Exception as e:
            clients = ClientModel.objects.all()
            return render(request, 'create_vehicle.html', {
                'clients': clients, 
                'error': f"Ocurrió un error inesperado: {str(e)}"
            })
    clients = ClientModel.objects.all()
    return render(request, 'create_vehicle.html', {'clients': clients})

def edit_vehicle_view(request, id):
    vehicle_obj = get_object_or_404(Vehicle, id=id)
    if request.method == 'POST':
        vehicle_obj.license_plate = request.POST['plate'].upper()
        vehicle_obj.type = request.POST['type']
        vehicle_obj.client_id = request.POST['client_id']
        vehicle_obj.save()
        return redirect('/vehiculos/')
    clients = ClientModel.objects.all()
    return render(request, 'edit_vehicle.html', {'vehicle': vehicle_obj, 'clients': clients})

def delete_vehicle_view(request, id):
    vehicle_obj = get_object_or_404(Vehicle, id=id)
    if request.method == 'POST':
        vehicle_obj.delete()
        return redirect('/vehiculos/')
    return render(request, 'delete_vehicle.html', {'vehicle': vehicle_obj})

#OPERACIONES DE PARQUEADERO (ENTRADA/SALIDA)

def entry_vehicle_view(request):
    if request.method == 'POST':
        plate_text = request.POST.get('license_plate', '').strip().upper()
        vehicle_type = request.POST.get('vehicle_type', 'CAR') 

        #Validaciones de la placa
        if not plate_text:
            return render(request, 'entry_vehicle.html', {'error': 'La placa es obligatoria'})
        
        if len(plate_text) > 6:
            return render(request, 'entry_vehicle.html', {'error': 'La placa no puede tener más de 6 caracteres'})

        #Lógica de Cliente y Vehículo
        cliente_gen, _ = ClientModel.objects.get_or_create(
            name="Visitante", defaults={'phone': '000'}
        )
        vehiculo_obj, created = Vehicle.objects.get_or_create(
            license_plate=plate_text,
            defaults={'client': cliente_gen, 'type': vehicle_type}
        )
        
        if not created and vehiculo_obj.type != vehicle_type:
             vehiculo_obj.type = vehicle_type
             vehiculo_obj.save()

        #Creación del Ticket
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

        # 1. Validación de longitud en salida
        if len(plate_text) > 6:
            messages.error(request, "La placa es inválida (máximo 6 caracteres)")
            return redirect('/salida/')

        try:
            vehicle_obj = Vehicle.objects.get(license_plate=plate_text)
            use_case = CloseTicket(DjangoTicketRepository(), DjangoParkingSpotRepository())
            total = use_case.execute(vehicle_obj)
            messages.success(request, f"Salida OK - Total: ${total}")
            return redirect('/salida/')
        except Vehicle.DoesNotExist:
            messages.error(request, f"La placa {plate_text} no existe")
        except Exception as e:
            messages.error(request, str(e))
            
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

from django.core.mail import send_mass_mail
from django.conf import settings

def enviar_recordatorio_cierre(request):

    #Tickets activos (vehículos dentro)
    tickets_activos = Ticket.objects.filter(status="ACTIVE").select_related("vehicle__client")

    mensajes = []

    for t in tickets_activos:
        cliente = t.vehicle.client

        if cliente.email:
            subject = "⏰ Parqueadero ParkPlace"
            message = f"""
Hola {cliente.name},

Tu vehículo con placa {t.vehicle.license_plate} sigue en el parqueadero.

⏳ Recuerda que faltan aproximadamente 20 minutos para el cierre.

Evita recargos adicionales retirándolo a tiempo.

— ParkPlace 🚗
"""
            mensajes.append((
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [cliente.email]
            ))

    if mensajes:
        send_mass_mail(mensajes, fail_silently=False)
        messages.success(request, "📩 Correos enviados correctamente")
    else:
        messages.warning(request, "⚠️ No hay clientes con email")

    return redirect("/dashboard/")