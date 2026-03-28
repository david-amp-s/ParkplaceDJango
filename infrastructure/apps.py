from django.apps import AppConfig

class InfrastructureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure'

    def ready(self):
        import sys
        if 'runserver' not in sys.argv:
            return

        from .models import ParkingSpot

        if ParkingSpot.objects.count() == 0:
            for i in range(1, 21):
                ParkingSpot.objects.create(number=i, status="AVAILABLE")