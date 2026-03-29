from django.contrib import admin
from django.urls import path
from infrastructure import views

from infrastructure.views import (
    login_view,
    logout_view,
    dashboard_view,
    list_employees,
    create_client_view,
    list_clients_view,
    edit_client_view,
    delete_client_view,
    create_vehicle_view,
    list_vehicles_view,
    edit_vehicle_view,
    delete_vehicle_view,
    entry_vehicle_view,
    exit_vehicle_view,
    pay_ticket_view,
    parking_status_view,
    history_view,
    reports_view,
    employee_create_view,
    employee_update_view,
    employee_delete_view,
    importar_clientes
)

urlpatterns = [
    
    path('admin/', admin.site.urls),

    #Autenticación y Login

    path('', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),

    #Empleados

    path('employee/', list_employees, name='list_employees'),
    path('employee/create/', employee_create_view, name='create_employee'),
    path('employee/update/<int:employee_id>/', employee_update_view, name='update_employee'),
    path('employee/delete/<int:employee_id>/', employee_delete_view, name='delete_employee'),
    #Clientes

    path('clientes/', list_clients_view, name='list_clients'),
    path('clientes/create/', create_client_view, name='create_client'),
    path('clientes/edit/<int:id>/', edit_client_view, name='edit_client'),
    path('clientes/delete/<int:id>/', delete_client_view, name='delete_client'),

    #Vehículos

    path('vehiculos/', list_vehicles_view, name='list_vehicles'),
    path('vehiculos/create/', create_vehicle_view, name='create_vehicle'),
    path('vehiculos/edit/<int:id>/', edit_vehicle_view, name='edit_vehicle'),
    path('vehiculos/delete/<int:id>/', delete_vehicle_view, name='delete_vehicle'),

    #Flujo de entrada/salida

    path('ingreso/', entry_vehicle_view, name='entry_vehicle'),
    path('salida/', exit_vehicle_view, name='exit_vehicle'),

    #Gestión de Espacios

    path('espacios/', parking_status_view, name='parking_spot_list'),
    path('gestion-espacios/', parking_status_view, name='parking_status'),

    #Pagos e Historial

    path('pay/', pay_ticket_view, name='pay_ticket'),
    path('historial/', history_view, name='historial'),

    #Correo

    path('enviar-recordatorio/', views.enviar_recordatorio_cierre),

    #Reportes
    path('reports/', reports_view, name='reports'),
    path('reports/download/', views.export_report_pdf, name='export_report_pdf'),

    #importar-clientes
    path('importar-clientes/', importar_clientes, name='importar_clientes'),
]