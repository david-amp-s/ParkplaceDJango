"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from infrastructure import views
from infrastructure.views import delete_client_view, delete_vehicle_view, login_view
from infrastructure.views import logout_view
from infrastructure.views import create_vehicle_view, list_vehicles_view, edit_vehicle_view
from infrastructure.views import create_client_view, edit_client_view, list_clients_view
from infrastructure.views import entry_vehicle_view, exit_vehicle_view
from django.contrib import admin 
from django.urls import path, include
from infrastructure.views import pay_ticket_view
from infrastructure.views import dashboard_view
from infrastructure.views import list_employees
urlpatterns = [

    path('admin/', admin.site.urls),
    
    path('', login_view),
    path('dashboard/', dashboard_view),
    path('logout/', logout_view),

    path('employee/', list_employees),

    path('clientes/create/', create_client_view),
    path('clientes/', list_clients_view),
    path('clientes/edit/<int:id>/', edit_client_view),

    path('vehiculos/', list_vehicles_view),
    path('vehiculos/create/', create_vehicle_view),
    path('vehiculos/edit/<int:id>/', edit_vehicle_view),

    path('clientes/delete/<int:id>/', delete_client_view),
    path('vehiculos/delete/<int:id>/', delete_vehicle_view),

    path('ingreso/', entry_vehicle_view),
    path('salida/', exit_vehicle_view),

    #payment

    path('pay/', pay_ticket_view, name = 'pay_ticket'),

    #historial

    path('historial/', views.history_view, name='historial'),

    #configuracion

    #path('configuracion/', configuration_view),
    #path('configuracion/reset/', reset_system_view),

    

    
]


