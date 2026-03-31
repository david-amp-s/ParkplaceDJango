from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0001_initial'),  # ajusta al nombre de tu última migración
    ]

    operations = [
        migrations.CreateModel(
            name='Tarifa',
            fields=[
                ('id', models.AutoField(primary_key=True)),
                ('tarifa_carro', models.IntegerField(default=3000)),
                ('tarifa_moto', models.IntegerField(default=2000)),
                ('descuento_registrado', models.IntegerField(default=20)),  # porcentaje
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'db_table': 'tarifa'},
        ),
    ]