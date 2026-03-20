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
from infrastructure.views import login_view
from infrastructure.views import logout_view
from infrastructure.views import create_client_view, create_vehicle_view, list_clients_view, list_vehicles_view


urlpatterns = [
    
    path('', login_view),
    path('logout/', logout_view),

    path('clientes/create/', create_client_view),
    path('clientes/', list_clients_view),

    path('vehiculos/', list_vehicles_view),
    path('vehiculos/create/', create_vehicle_view),
    path('', create_client_view)

]
