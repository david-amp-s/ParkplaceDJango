import traceback

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now, timedelta
from django.db.models import Q, Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from django.db import IntegrityError
from django.core.mail import send_mass_mail
from django.conf import settings

# Modelos de Infraestructura
from .models import ParkingSpot, Vehicle, Client as ClientModel, Ticket

from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from .models import ParkingSpot, Ticket
# Formularios
from .forms import ClientForm

# Repositorios
from .repositories import (
    DjangoClientRepository,
    DjangoVehicleRepository,
    DjangoPaymentRepository,
    DjangoEmployeeRepository,
    DjangoTicketRepository,
    DjangoParkingSpotRepository
    
)

# Entidades de Dominio
from domain.entities.employee import Employee
from domain.entities.client import Client as ClientEntity
from domain.entities.vehicle import Vehicle as VehicleEntity

# Casos de Uso
from domain.use_cases.login_user import LoginUser
from domain.use_cases.create_client import CreateClient
from domain.use_cases.create_vehicle import CreateVehicle
from domain.use_cases.pay_ticket import PayticketUseCase
from domain.use_cases.create_ticket import CreateTicket
from domain.use_cases.get_history import GetHistory
from domain.use_cases.close_ticket import CloseTicket


# AUTENTICACIÓN Y LOGOUT

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        repo = DjangoEmployeeRepository()
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


# DASHBOARD Y ESPACIOS


def dashboard_view(request):
    fecha_hoy = now().date()
    # Definimos el inicio de la semana
    hace_una_semana = fecha_hoy - timedelta(days=7)

    vehiculos_hoy = Ticket.objects.filter(created_at__date=fecha_hoy).count()
    
    ingresos_hoy = Ticket.objects.filter(
        exit_time__date=fecha_hoy,
        status="CLOSED"
    ).aggregate(
        total=Coalesce(Sum("total_paid"), 0, output_field=DecimalField())
    )["total"]

    total_spots = ParkingSpot.objects.count()
    occupied_count = ParkingSpot.objects.filter(status="OCCUPIED").count()
    ocupacion = int((occupied_count / total_spots) * 100) if total_spots > 0 else 0

    vehiculos_por_tipo = (
        Ticket.objects
        .filter(created_at__date=fecha_hoy)
        .values("vehicle__type")
        .annotate(total=Count("id"))
    )

    clientes_frecuentes = (
        Ticket.objects
        .filter(created_at__date__gte=hace_una_semana)
        .values("vehicle__client__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    actividades = (
        Ticket.objects
        .select_related("vehicle")
        .order_by("-created_at")[:5]
    )

    context = {
        "vehiculos_hoy": vehiculos_hoy,
        "ingresos_hoy": ingresos_hoy,
        "ocupacion_actual": ocupacion,
        "clientes_frecuentes": clientes_frecuentes,
        "actividades_recientes": actividades,
        "tipos": [v["vehicle__type"] for v in vehiculos_por_tipo],
        "cantidades": [v["total"] for v in vehiculos_por_tipo],
    }

    return render(request, "dashboard.html", context)

def parking_status_view(request):
    repo = DjangoParkingSpotRepository()
    all_spots_from_db = repo.get_all()

    spots_with_info = []

    #EspaciosXtickets
    for spot in all_spots_from_db:
        ticket = None
        is_occupied = (spot.status == "OCCUPIED")

        if is_occupied:
            #Buscamos el tickets ocupados
            ticket = Ticket.objects.filter(parking_spot=spot, status='ACTIVE').first()

        spots_with_info.append({
            "spot": spot,
            "ticket": ticket,
            "is_occupied": is_occupied
        })

    return render(request, "parking_status.html", {
        "all_spots": spots_with_info
    })


# GESTIÓN DE EMPLEADOS

def list_employees(request):
    repo = DjangoEmployeeRepository()
    employees = repo.get_all()
    return render(request, "list_employees.html", {"employees": employees})


def create_employee(request):
    if request.method == "POST":
        employee = Employee(
            id=None,
            name=request.POST["name"],
            phone=request.POST["phone"],
            username=request.POST["username"],
            password=request.POST["password"],
            role="EMPLOYEE",
            created_at=None
        )
        repo = DjangoEmployeeRepository()
        repo.create(employee)
        return redirect("/employee/")

    return render(request, "create_employee.html")


# GESTIÓN DE CLIENTES

def list_clients_view(request):

    query = request.GET.get('q', '').strip()
    
    # Base de clientes
    clients = ClientModel.objects.all()

    if query:
        clients = clients.filter(name__icontains=query)

    context = {
        'clients': clients.order_by('id'),
        'query': query
    }
    
    return render(request, 'list_clients.html', context)


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


def edit_client_view(request, id):
    client_obj = get_object_or_404(ClientModel, id=id)

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():

            data = form.cleaned_data
            client_obj.name = data['name']
            client_obj.phone = data['phone']
            client_obj.email = data.get('email')
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


# GESTIÓN DE VEHÍCULOS

from django.db.models import Q

def list_vehicles_view(request):

    query = request.GET.get('q', '').strip()
    registrados = Vehicle.objects.exclude(
        Q(client__name__icontains="Visitante") | Q(client__isnull=True)
    )

    #Definimos la base de VISITANTES
    visitantes = Vehicle.objects.filter(
        Q(client__name__icontains="Visitante") | Q(client__isnull=True)
    )

    if query:
        search_filter = Q(license_plate__icontains=query) | Q(client__name__icontains=query)
        
        registrados = registrados.filter(search_filter)
        visitantes = visitantes.filter(search_filter)

    context = {
        'registrados': registrados.order_by('id'),
        'visitantes': visitantes.order_by('-id'),
        'query': query
    }
    
    return render(request, 'list_vehicles.html', context)

def create_vehicle_view(request):
    if request.method == 'POST':
        plate = request.POST.get('plate', '').strip().upper()
        vehicle_type = request.POST.get('type')
        client_id = request.POST.get('client_id')

        if not client_id:
            clients = ClientModel.objects.all()
            return render(request, 'create_vehicle.html', {
                'clients': clients,
                'error': "Debes seleccionar un cliente. Para visitantes ocasionales, usa el registro de entrada directo."
            })

        #Filtro de seguridad
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


# OPERACIONES DE PARQUEADERO (ENTRADA/SALIDA)

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

        #Validación en salida
        if len(plate_text) > 6:
            messages.error(request, "La placa es inválida (máximo 6 caracteres)")
            return redirect('/salida/')

        try:
            vehicle_obj = Vehicle.objects.get(license_plate=plate_text)
            use_case = CloseTicket(DjangoTicketRepository(), DjangoParkingSpotRepository())
            total = use_case.execute(vehicle_obj)
            messages.success(request, f"Salida Registrada - Total: ${total}")
            return redirect('/salida/')
        except Vehicle.DoesNotExist:
            messages.error(request, f"La placa {plate_text} no existe")
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'exit_vehicle.html')


# PAGOS E HISTORIAL

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


def enviar_recordatorio_cierre(request):

    #Tickets activos
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
        messages.warning(request, "No hay clientes con email")

    return redirect("/dashboard/")

#Reportes

"""
Agrega estas vistas al archivo views.py existente de infrastructure.
Importa las clases necesarias al inicio del archivo.
"""

from django.shortcuts import render
from datetime import datetime

from infrastructure.report_repository_impl import DjangoReportRepository
from domain.use_cases.get_reports import GetReportsUseCase


# Instancia compartida (o puedes crearla dentro de cada vista si prefieres)
def _get_report_use_case():
    return GetReportsUseCase(DjangoReportRepository())


from datetime import datetime

def reports_dashboard(request):
    uc = _get_report_use_case()

    # Filtros
    selected_year  = int(request.GET.get("year", datetime.today().year))
    selected_month = int(request.GET.get("month", datetime.today().month))
    selected_date  = request.GET.get("date", str(datetime.today().date()))

    # Validación de fecha
    try:
        daily_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        daily_date = datetime.today().date()

    # REPORTES (USE CASE)
    daily_income = uc.get_daily_income(daily_date)
    monthly_income = uc.get_monthly_income(selected_year, selected_month)
    vehicle_stats = uc.get_vehicle_type_stats()
    frequent_clients = uc.get_frequent_clients(limit=10)
    usage_stats = uc.get_usage_stats()

    # 🔥 VALIDACIONES SEGURAS (evita None)
    total_tickets = usage_stats.get("total_tickets", 0) if usage_stats else 0
    total_income = daily_income.get("total", 0) if daily_income else 0

    # 🔥 PROMEDIO TICKET
    average_ticket = (
        total_income / total_tickets if total_tickets > 0 else 0
    )

    context = {
        "selected_year": selected_year,
        "selected_month": selected_month,
        "selected_date": str(daily_date),

        # Meses
        "months": [
            (1,"Enero"),(2,"Febrero"),(3,"Marzo"),(4,"Abril"),
            (5,"Mayo"),(6,"Junio"),(7,"Julio"),(8,"Agosto"),
            (9,"Septiembre"),(10,"Octubre"),(11,"Noviembre"),(12,"Diciembre"),
        ],

        # Años dinámicos (evita hardcode)
        "years": list(range(2023, datetime.today().year + 1)),

        # 🔥 DATOS QUE USA TU HTML
        "daily_income": daily_income or {"total": 0},
        "monthly_income": monthly_income or [],
        "income_by_vehicle_type": vehicle_stats or [],
        "top_revenue_days": monthly_income or [],
        "client_type_stats": frequent_clients or [],
        "usage_stats": usage_stats or {},

        # 🔥 KPIs
        "average_ticket": round(average_ticket, 2),
        "occupancy_rate": usage_stats.get("occupancy_rate", 0) if usage_stats else 0,
    }

    return render(request, "reports.html", context)