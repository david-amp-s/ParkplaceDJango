import re
import traceback
import os
import base64
import math
from datetime import date, timedelta
from decimal import Decimal
from .decorators import login_required, admin_required

from .utils import build_history_excel

#Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from django.db.models import Q, Sum, Count, DecimalField
from django.db.models.functions import Coalesce
from django.db import IntegrityError
from django.core.mail import send_mass_mail, EmailMessage
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponse


#Utilidades e Infraestructura
from domain.use_cases.client_import_service import ClientImportService
from infrastructure.utils import render_to_pdf
from .models import ParkingSpot, Vehicle, Client as ClientModel, Ticket, Client, EmployeeModel, Tarifa
from .services import WeatherService

#Formularios
from .forms import ClientForm

#Repositorios
from .repositories import (
    DjangoClientRepository,
    DjangoReportRepository,
    DjangoVehicleRepository,
    DjangoPaymentRepository,
    DjangoEmployeeRepository,
    DjangoTicketRepository,
    DjangoParkingSpotRepository
)

#Entidades de Dominio
from domain.entities.employee import Employee
from domain.entities.client import Client as ClientEntity
from domain.entities.vehicle import Vehicle as VehicleEntity

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

#DASHBOARD

@login_required
def dashboard_view(request):
    fecha_hoy = now().date()
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

    estado_clima = WeatherService.get_clima_bogota()

    context = {
        "vehiculos_hoy": vehiculos_hoy,
        "ingresos_hoy": ingresos_hoy,
        "ocupacion_actual": ocupacion,
        "clientes_frecuentes": clientes_frecuentes,
        "actividades_recientes": actividades,
        "tipos": [v["vehicle__type"] for v in vehiculos_por_tipo],
        "cantidades": [v["total"] for v in vehiculos_por_tipo],
        "clima": estado_clima,
    }

    return render(request, "dashboard.html", context)

#ESPACIOS

@login_required
def parking_status_view(request):
    repo = DjangoParkingSpotRepository()
    all_spots_from_db = repo.get_all()
    spots_with_info = []

    for spot in all_spots_from_db:
        ticket = None
        is_occupied = (spot.status == "OCCUPIED")
        tiempo = None

        if is_occupied:
            ticket = Ticket.objects.filter(
                parking_spot=spot,
                status='ACTIVE'
            ).first()

            if ticket:
                duracion = now() - ticket.entry_time
                minutos = math.floor(duracion.total_seconds() / 60)
                tiempo = minutos

        spots_with_info.append({
            "spot": spot,
            "ticket": ticket,
            "is_occupied": is_occupied,
            "tiempo": tiempo
        })

    return render(request, "parking_status.html", {
        "all_spots": spots_with_info
    })

#GESTION DE EMPLEADOS

@admin_required
def list_employees(request):
    repo = DjangoEmployeeRepository()
    employees = repo.get_all()
    return render(request, "list_employees.html", {"employees": employees})


@admin_required
def employee_create_view(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone")
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        role = request.POST.get("role")

        if len(name) > 15:
            messages.error(request, "El nombre no puede superar los 15 caracteres.")
            return render(request, "create_employee.html")

        if len(username) > 15:
            messages.error(request, "El usuario no puede superar los 15 caracteres.")
            return render(request, "create_employee.html")

        hashed_password = make_password(password)

        EmployeeModel.objects.create(
            name=name,
            phone=phone,
            username=username,
            password=hashed_password,
            role=role
        )
        return redirect("/employee/")

    return render(request, "create_employee.html")


@admin_required
def employee_update_view(request, employee_id):
    employee = get_object_or_404(EmployeeModel, id=employee_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        username = request.POST.get("username", "").strip()

        if len(name) > 15:
            messages.error(request, "El nombre no puede superar los 15 caracteres.")
            return render(request, "update_employee.html", {"employee": employee})

        if len(username) > 15:
            messages.error(request, "El usuario no puede superar los 15 caracteres.")
            return render(request, "update_employee.html", {"employee": employee})

        employee.name = name
        employee.phone = request.POST.get("phone")
        employee.username = username
        employee.role = request.POST.get("role")

        password = request.POST.get("password")
        if password:
            employee.password = make_password(password)

        employee.save()
        return redirect("/employee/")

    return render(request, "update_employee.html", {"employee": employee})


@admin_required
def employee_delete_view(request, employee_id):
    employee = get_object_or_404(EmployeeModel, id=employee_id)

    if request.method == "POST":
        employee.delete()
        return redirect("/employee/")

    context = {"employee": employee}
    return render(request, "delete_employee.html", context)

#GESTION DE CLIENTES

@login_required
def list_clients_view(request):
    query = request.GET.get('q', '').strip()
    clients = ClientModel.objects.all()

    if query:
        clients = clients.filter(name__icontains=query)

    context = {
        'clients': clients.order_by('id'),
        'query': query
    }

    return render(request, 'list_clients.html', context)


@login_required
def create_client_view(request):
    form = ClientForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            nombre = data['name']

            if not re.match(r"^[a-zA-ZÁÉÍÓÚáéíóúñÑ\s]+$", nombre):
                messages.error(request, "El nombre del cliente solo puede contener letras.")
                return render(request, 'create_client.html', {'form': form})

            if len(nombre.strip()) > 15:
                messages.error(request, "El nombre del cliente no puede superar los 15 caracteres.")
                return render(request, 'create_client.html', {'form': form})

            repo = DjangoClientRepository()
            use_case = CreateClient(repo)

            use_case.execute(
                nombre,
                data['phone'],
                data.get('email'),
                data.get('client_type', 'REGULAR')
            )

            messages.success(request, "Cliente creado correctamente")
            return redirect('/clientes/')
        else:
            messages.error(request, "Error en el formulario")

    return render(request, 'create_client.html', {'form': form})


@login_required
def edit_client_view(request, id):
    client_obj = get_object_or_404(Client, id=id)

    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            nuevo_nombre = data['name']

            if not re.match(r"^[a-zA-ZÁÉÍÓÚáéíóúñÑ\s]+$", nuevo_nombre):
                messages.error(request, "El nombre del cliente no puede contener números ni caracteres especiales.")
                return render(request, 'edit_client.html', {'form': form, 'client': client_obj})

            if len(nuevo_nombre.strip()) > 15:
                messages.error(request, "El nombre del cliente no puede superar los 15 caracteres.")
                return render(request, 'edit_client.html', {'form': form, 'client': client_obj})

            client_obj.name = nuevo_nombre
            client_obj.phone = data['phone']
            client_obj.email = data.get('email')

            if 'client_type' in data:
                client_obj.client_type = data['client_type']

            client_obj.save()
            messages.success(request, f"Cliente {client_obj.name} actualizado correctamente.")
            return redirect('/clientes/')
        else:
            messages.error(request, "Error al validar los datos del formulario.")
    else:
        form = ClientForm(initial={
            'name': client_obj.name,
            'phone': client_obj.phone,
            'email': client_obj.email,
            'client_type': getattr(client_obj, 'client_type', 'REGULAR')
        })

    return render(request, 'edit_client.html', {'form': form, 'client': client_obj})

@login_required
def delete_client_view(request, id):
    client_obj = get_object_or_404(Client, id=id)

    if request.method == 'POST':
        tiene_movimiento_activo = Ticket.objects.filter(
            vehicle__client=client_obj,
            status='ACTIVE'
        ).exists()

        if tiene_movimiento_activo:
            messages.error(
                request,
                f"No se puede eliminar a {client_obj.name} porque uno de sus vehículos está actualmente en el parqueadero."
            )
            return redirect('/clientes/')

        nombre_cliente = client_obj.name
        client_obj.delete()
        messages.success(request, f"Cliente {nombre_cliente} eliminado correctamente.")
        return redirect('/clientes/')

    return render(request, 'delete_client.html', {'client': client_obj})

#GESTION DE VEHICULOS

@login_required
def list_vehicles_view(request):
    query = request.GET.get('q', '').strip()
    registrados = Vehicle.objects.exclude(
        Q(client__name__icontains="Visitante") | Q(client__isnull=True)
    )

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


@login_required
def create_vehicle_view(request):
    if request.method == 'POST':
        plate = request.POST.get('plate', '').strip().upper()
        vehicle_type = request.POST.get('type')
        client_id = request.POST.get('client_id')

        if not client_id:
            clients = ClientModel.objects.all()
            return render(request, 'create_vehicle.html', {
                'clients': clients,
                'error': "Debes seleccionar un cliente."
            })

        if len(plate) > 6:
            clients = ClientModel.objects.all()
            return render(request, 'create_vehicle.html', {
                'clients': clients,
                'error': f"La placa '{plate}' es demasiado larga (máx 6)."
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
                'error': f"Error: {str(e)}"
            })

    clients = ClientModel.objects.all()
    return render(request, 'create_vehicle.html', {'clients': clients})


@login_required
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


@login_required
def delete_vehicle_view(request, id):
    vehicle_obj = get_object_or_404(Vehicle, id=id)

    if request.method == 'POST':
        esta_en_parqueadero = Ticket.objects.filter(
            vehicle=vehicle_obj,
            status='ACTIVE'
        ).exists()

        if esta_en_parqueadero:
            messages.error(
                request,
                f"No se puede eliminar el vehículo {vehicle_obj.license_plate} porque tiene un proceso activo."
            )
            return redirect('/vehiculos/')

        placa = vehicle_obj.license_plate
        vehicle_obj.delete()
        messages.success(request, f"Vehículo con placa {placa} eliminado exitosamente.")
        return redirect('/vehiculos/')

    return render(request, 'delete_vehicle.html', {'vehicle': vehicle_obj})

#GESTION DE INGRESO Y SALIDA

@login_required
def entry_vehicle_view(request):
    if request.method == 'POST':
        plate_text = request.POST.get('license_plate', '').strip().upper()
        vehicle_type = request.POST.get('vehicle_type', 'CAR')

        if not plate_text:
            return render(request, 'entry_vehicle.html', {'error': 'La placa es obligatoria'})

        if len(plate_text) > 6:
            return render(request, 'entry_vehicle.html', {'error': 'Placa inválida (máx 6)'})

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

        use_case = CreateTicket(DjangoTicketRepository(), DjangoParkingSpotRepository())
        try:
            use_case.execute(vehiculo_obj.id, None)
            messages.success(request, f"Ingreso: {plate_text}")
            return redirect('/ingreso/')
        except Exception as e:
            return render(request, 'entry_vehicle.html', {'error': str(e)})

    return render(request, 'entry_vehicle.html')


@login_required
def exit_vehicle_view(request):

    # limpiar session si viene ?clear=1
    if request.GET.get('clear'):
        request.session.pop('last_ticket_id', None)

    if request.method == 'POST':
        plate_text = request.POST.get('license_plate', '').strip().upper()

        if len(plate_text) > 6:
            messages.error(request, "La placa es inválida.")
            return redirect('/salida/')

        try:
            vehicle_obj = Vehicle.objects.get(license_plate=plate_text)

            use_case = CloseTicket(
                DjangoTicketRepository(),
                DjangoParkingSpotRepository()
            )
            ticket = use_case.execute(vehicle_obj)

            duracion = ticket.exit_time - ticket.entry_time
            minutos = math.ceil(duracion.total_seconds() / 60)

            context = {
                "ticket": ticket,
                "vehicle": vehicle_obj,
                "cliente": vehicle_obj.client,
                "minutos": minutos,
                "fecha_entrada": ticket.entry_time,
                "fecha_salida": ticket.exit_time,
                "total": ticket.total_paid,
            }

            pdf = render_to_pdf('factura_pdf.html', context)
            cliente = vehicle_obj.client

            if pdf and cliente and cliente.email:
                try:
                    email = EmailMessage(
                        subject="Factura ParkPlace",
                        body=f"""
Hola {cliente.name},

Tu vehículo con placa {vehicle_obj.license_plate} ha salido del parqueadero.

Adjuntamos tu factura.
""",
                        from_email=settings.EMAIL_HOST_USER,
                        to=[cliente.email],
                    )
                    email.attach(
                        f"factura_{plate_text}_{ticket.id}.pdf",
                        pdf,
                        "application/pdf"
                    )
                    email.send()
                except Exception as e:
                    print("Error enviando correo:", e)

            # guardar ticket en session
            request.session['last_ticket_id'] = ticket.id

            return redirect('/salida/')

        except Vehicle.DoesNotExist:
            messages.error(request, f"No se encontró ningún vehículo con la placa {plate_text}.")
        except Exception as e:
            messages.error(request, str(e))

    # recuperar ticket
    ticket_id = request.session.get('last_ticket_id')

    ticket = None
    total = None
    placa = None

    if ticket_id:
        try:
            ticket = Ticket.objects.get(id=ticket_id)
            total = ticket.total_paid
            placa = ticket.vehicle.license_plate
        except:
            request.session.pop('last_ticket_id', None)
            ticket_id = None

    return render(request, 'exit_vehicle.html', {
        'ticket_id': ticket_id,
        'total': total,
        'placa': placa,
        "cliente_nombre": ticket.vehicle.client.name if ticket else None,
    })

#TICKET

@admin_required
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

#HISTORIAL

@login_required
def history_view(request):
    query = request.GET.get('q', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    repo = DjangoTicketRepository()
    tickets = Ticket.objects.all().order_by('-created_at')

    if query:
        tickets = tickets.filter(vehicle__license_plate__icontains=query)

    if fecha_inicio:
        tickets = tickets.filter(created_at__date__gte=fecha_inicio)

    if fecha_fin:
        tickets = tickets.filter(created_at__date__lte=fecha_fin)

    return render(request, 'list_history.html', {
        'tickets': tickets,
        'query': query,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    })

#CORREO DE AVISO DE CIERRE

@login_required
def enviar_recordatorio_cierre(request):
    tickets_activos = Ticket.objects.filter(status="ACTIVE").select_related("vehicle__client")
    mensajes = []

    for t in tickets_activos:
        cliente = t.vehicle.client
        if cliente.email:
            subject = "Parqueadero ParkPlace"
            message = f"Hola {cliente.name}, tu vehículo con placa {t.vehicle.license_plate} sigue aquí. Faltan 20 min para el cierre. ⏰"
            mensajes.append((
                subject, message, settings.EMAIL_HOST_USER, [cliente.email]
            ))

    if mensajes:
        send_mass_mail(mensajes, fail_silently=False)
        messages.success(request, "Correos enviados")
    else:
        messages.warning(request, "No hay clientes con email")
    return redirect("/dashboard/")

#REPORTES

@admin_required
def reports_view(request):
    repo = DjangoReportRepository()
    finanzas = repo.get_financial_summary()
    comparativo_dias = repo.get_revenue_by_day_of_week()
    stay_metrics = repo.get_stay_metrics()
    vehicle_stats = repo.get_vehicle_type_stats()
    monthly_income = repo.get_monthly_income()
    horas_pico = repo.get_peak_hours()

    total_spots = ParkingSpot.objects.count()
    occupied_count = ParkingSpot.objects.filter(status="OCCUPIED").count()
    ocupacion = int((occupied_count / total_spots) * 100) if total_spots > 0 else 0

    average_ticket = finanzas['hoy'] / finanzas['tickets_hoy'] if finanzas['tickets_hoy'] > 0 else 0

    context = {
        "finanzas": finanzas,
        "comparativo_dias": comparativo_dias,
        "monthly_income": monthly_income,
        "average_ticket": average_ticket,
        "stay_avg": stay_metrics['avg_time'],
        "stay_max": stay_metrics['max_time'],
        "occupancy_rate": ocupacion,
        "vehicle_stats": vehicle_stats,
        "horas_pico": horas_pico,
        "hoy": date.today(),
    }
    return render(request, "reports.html", context)

#REPORTES PDF

@login_required
def export_report_pdf(request):
    repo = DjangoReportRepository()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path_al_logo = os.path.join(current_dir, 'assets', 'pezokoi.png')

    try:
        with open(path_al_logo, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            logo_base64 = f"data:image/png;base64,{encoded_string}"
    except:
        logo_base64 = ""

    finanzas_raw = repo.get_financial_summary() or {}
    context = {
        "finanzas": {
            "hoy": finanzas_raw.get('hoy') or Decimal('0.00'),
            "semana": finanzas_raw.get('semana') or Decimal('0.00'),
            "mes": finanzas_raw.get('mes') or Decimal('0.00'),
        },
        "horas_pico": list(repo.get_peak_hours() or []),
        "stay_avg": (repo.get_stay_metrics() or {}).get('avg_time') or 0,
        "stay_max": (repo.get_stay_metrics() or {}).get('max_time') or 0,
        "vehicle_stats": list(repo.get_vehicle_type_stats() or []),
        "hoy": date.today(),
        "logo_base64": logo_base64
    }

    pdf = render_to_pdf('reports_pdf.html', context)

    if pdf:
        return HttpResponse(pdf, content_type='application/pdf')

    return HttpResponse("Error generando PDF", status=500)

#CARGA MASIVA DE DATOS

@login_required
def importar_clientes(request):
    try:
        total = ClientImportService.import_from_java()
        return JsonResponse({
            "success": True,
            "message": f"{total} clientes importados correctamente"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=500)

#TARIFA

@admin_required
def tarifa_view(request):
    config = Tarifa.get_config()

    if request.method == 'POST':
        try:
            tarifa_carro = int(request.POST.get('tarifa_carro', 0))
            tarifa_moto = int(request.POST.get('tarifa_moto', 0))
            descuento = int(request.POST.get('descuento_registrado', 0))

            if tarifa_carro <= 0 or tarifa_moto <= 0:
                raise ValueError("Las tarifas deben ser mayores a 0")
            if not (0 <= descuento <= 100):
                raise ValueError("El descuento debe estar entre 0 y 100")

            config.tarifa_carro = tarifa_carro
            config.tarifa_moto = tarifa_moto
            config.descuento_registrado = descuento
            config.save()

            messages.success(request, "Tarifas actualizadas correctamente.")
            return redirect('/tarifas/')
        except ValueError as e:
            messages.error(request, str(e))

    return render(request, 'tarifas.html', {'config': config})

#FACTURA PDF

@login_required
def descargar_factura_view(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    vehicle_obj = ticket.vehicle
    duracion = ticket.exit_time - ticket.entry_time
    minutos = math.ceil(duracion.total_seconds() / 60)

    context = {
        "ticket": ticket,
        "vehicle": vehicle_obj,
        "cliente": vehicle_obj.client,
        "minutos": minutos,
        "fecha_entrada": ticket.entry_time,
        "fecha_salida": ticket.exit_time,
        "total": ticket.total_paid,
    }

    pdf = render_to_pdf('factura_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_{vehicle_obj.license_plate}_{ticket.id}.pdf"'
        return response

    return HttpResponse("Error generando PDF", status=500)

#PERFIL DE CLIENTE

@login_required
def client_profile_view(request, id):
    client_obj = get_object_or_404(Client, id=id)

    vehiculos = Vehicle.objects.filter(client=client_obj)

    tickets = Ticket.objects.filter(
        vehicle__client=client_obj
    ).order_by('-created_at')

    total_visitas = tickets.count()
    total_pagado = tickets.aggregate(
        total=Coalesce(Sum("total_paid"), 0, output_field=DecimalField())
    )["total"]

    context = {
        "cliente": client_obj,
        "vehiculos": vehiculos,
        "tickets": tickets[:10],
        "total_visitas": total_visitas,
        "total_pagado": total_pagado,
    }
    return render(request, "client_profile.html", context)

#HISTORIAL EXCEL

from .utils import build_history_excel

@admin_required
def export_history_excel(request):
    tickets = Ticket.objects.select_related('vehicle__client', 'parking_spot').all()

    wb = build_history_excel(tickets)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=historial.xlsx'

    wb.save(response)
    return response