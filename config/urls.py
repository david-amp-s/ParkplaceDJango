from django.contrib import admin
from django.urls import path

from infrastructure.views import (
    login_view,
    logout_view,
    dashboard_view,

    list_employees,

    create_client_view,
    list_clients_view,
    edit_client_view,

    create_vehicle_view,
    list_vehicles_view,
    edit_vehicle_view,

    entry_vehicle_view,
    exit_vehicle_view,

    pay_ticket_view,

    parking_spot_list,
    parking_status_view   # 👈 NUEVO
)

urlpatterns = [

    path('admin/', admin.site.urls),

    # 🔐 auth
    path('', login_view),
    path('dashboard/', dashboard_view),
    path('logout/', logout_view),

    # 👷 empleados
    path('employee/', list_employees),

    # 👥 clientes
    path('clientes/create/', create_client_view),
    path('clientes/', list_clients_view),
    path('clientes/edit/<int:id>/', edit_client_view),

    # 🚗 vehículos
    path('vehiculos/', list_vehicles_view),
    path('vehiculos/create/', create_vehicle_view),
    path('vehiculos/edit/<int:id>/', edit_vehicle_view),

    # 🚗 flujo
    path('ingreso/', entry_vehicle_view),
    path('salida/', exit_vehicle_view),

    # 🅿️ espacios
    path('espacios/', parking_spot_list, name='parking_spot_list'),
    path('gestion-espacios/', parking_status_view, name='parking_status'),  # 👈 NUEVO

    # 💳 pagos
    path('pay/', pay_ticket_view, name='pay_ticket'),
]