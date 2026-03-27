from django.db import migrations

def crear_espacios_iniciales(apps, schema_editor):
    ParkingSpot = apps.get_model('infrastructure', 'ParkingSpot')
    
    # En lugar de bulk_create, vamos uno por uno para que Postgres no llore
    for i in range(1, 31):
        # get_or_create evita que falle si por alguna razón ya existe el número
        ParkingSpot.objects.get_or_create(
            number=i,
            defaults={
                'type': 'CAR', 
                'status': 'AVAILABLE'
            }
        )

class Migration(migrations.Migration):

    dependencies = [
        # ESTO ES VITAL: Le dice a Django "Primero ejecuta el 0001_initial"
        ('infrastructure', '0001_initial'), 
    ]

    operations = [
        migrations.RunPython(crear_espacios_iniciales),
    ]